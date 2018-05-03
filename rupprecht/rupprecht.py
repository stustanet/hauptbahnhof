#!/usr/bin/env python3

import asyncio
import json
import serial_asyncio
import serial

from hauptbahnhof import Hauptbahnhof

from . import rcswitch

class RupprechtError:
    pass

class RupprechtCommandError(RupprechtError):
    def __init__(self, command):
        self.command = command

    def __repr__(self):
        return "RupprechtCommandError: {}".format(self.command)

class Rupprecht:
    """
    Implement serial connection to rupprecht
    """

    def __init__(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.hbf = Hauptbahnhof(loop)
        self.hbf.subscribe('/haspa/led', self.command_led)
        self.space_is_open = False

        try:
            r = RupprechtInterface("/dev/ttyACM0")
        except serial.SerialException:
            r = RupprechtInterface("/tmp/rupprechtemulator")

        r.subscribe_button(self.button_message)

        self.imposed_ids = {
            'rupprecht-table': rcswitch.Quigg1000(code=1337, subaddr=1, rupprecht=r),
            'rupprecht-alarm': rcswitch.Quigg1000(code=1337, subaddr=2, rupprecht=r),
            'rupprecht-fan': rcswitch.Quigg1000(code=1337, subaddr=3, rupprecht=r)
        }

    async def teardown(self):
        await self.hbf.teardown()

    async def command_led(self, source, payload, msg):
        for devid, value in msg.items():
            try:
                if value == 0:
                    self.imposed_ids[devid].off()
                elif value == 1023:
                    self.imposed_ids[devid].on()
            except KeyError:
                pass

    async def button_message(self, msg):
        if msg['open'] and not self.space_is_open:
            self.space_is_open = True
            await self.hbf.publish('/haspa/status', 'open')
        elif not msg['open'] and self.space_is_open:
            self.space_is_open = False
            await self.hbf.publish('/haspa/status', 'closed')

class RupprechtInterface:
    class SerialProtocol(asyncio.Protocol):
        def __init__(self, master):
            self.master = master
            self.buffer = []

        def connection_made(self, transport):
            #transport.serial.rts = False
            self.master.transport = transport

        def data_received(self, data):
            for d in data:
                if chr(d) == '\n':
                    self.master.received(self.buffer)
                    self.buffer = []
                else:
                    self.buffer.append(chr(d))

        def connection_lost(self, exc):
            print('port closed, exiting')
            self.master.loop.stop()


    def __init__(self, serial_port, baudrate=115200, loop=None):
        if loop == None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.transport = None
        self.response_pending = False
        self._queue = []
        self.response_event = asyncio.Event(loop=loop)
        self.ready = False
        self.ready_event = asyncio.Event(loop=loop)
        self.button_callbacks = [];
        self.last_result = ''
        coro = serial_asyncio.create_serial_connection(loop,
                (lambda: RupprechtInterface.SerialProtocol(self)),
                serial_port, baudrate=baudrate)
        loop.run_until_complete(coro)
        self.echo_allowed = True

    def subscribe_button(self, callback):
        self.button_callbacks.append(callback)

    async def send_raw(self, msg, expect_response=True, force=False):
        """
        Send the raw line to the serial stream

        This will wait, until the preceding message has been processed.
        """
        if not self.ready:
            print("Waiting for client to become ready")
            await self.ready_event.wait()
            print("Client is now ready")

        if self.echo_allowed and "CONFIG ECHO" not in msg:
            await self.send_raw("CONFIG ECHO OFF")

        # The queue is the message stack that has to be processed
        self._queue.append(msg)
        while self._queue:
            self.response_event.clear()
            # Await, if there was another message in the pipeline that has not
            # yet been processed
            if not force:
                while self.response_pending:
                    print("before sending '{}' we need a response for '{}'".format(msg, self.last_command))
                    await self.response_event.wait()
                    self.response_event.clear()
            print("Sending", msg)
            # If the queue has been processed by somebody else in the meantime
            if not self._queue:
                break
            self.response_pending = True
            next_msg = self._queue.pop(0)

            # Now actually send the data
            self.last_command = next_msg
            self.transport.write(next_msg.encode('ascii'))
            #append a newline if the sender hasnt already
            if next_msg[-1] != '\n':
                self.transport.write(b'\n')

            await self.response_event.wait()
            self.response_event.clear()
            try:
                if str.startswith(self.last_result, "ERROR"):
                    raise RupprechtCommandError(msg)
                elif str.startswith(self.last_result, "OK"):
                    if self.last_command == "CONFIG ECHO OFF":
                        self.echo_allowed = False
                    self.response_pending = False
                    self.response_event.set()
                    return True
                else:
                    if not expect_response:
                        self.response_pending = False
                        return True
                    #raise RupprechtCommandError("Unknown result code: {}".format(self.last_result))
            except Exception as e:
                print("Exception while parsing response", msg, e)
                break

    def received(self, msg):
        msg = ''.join(msg).strip()
        if not msg:
            return
        print("received \033[03m{}\033[0m".format(msg))
        if str.startswith(msg, "BUTTON"):
            try:
                self.buttons = json.loads(msg[len("BUTTON"):])
                asyncio.gather(*[b(self.buttons) for b in self.button_callbacks], loop=self.loop)
            except json.decoder.JSONDecodeError:
                print("Invalid json received:", msg)
        elif msg == "READY" and not self.ready:
            self.ready = True
            self.ready_event.set()
        else:
            self.last_result = msg
            self.response_event.set()

    async def help(self):
        await self.send_raw("HELP")

    async def config(self, key, value):
        await self.send_raw("CONFIG {} {}".format(key, value))

    async def text(self, msg):
        await self.send_raw("TEXT {}".format(msg), expect_response=False)

    async def button(self):
        await self.send_raw("BUTTON", expect_response=False)

    async def light(self, raw_msg):
        await self.send_raw("LIGHT {}".format(raw_msg), expect_response=False)
