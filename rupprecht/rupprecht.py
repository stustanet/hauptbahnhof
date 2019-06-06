#!/usr/bin/env python3

import asyncio
import json
import serial_asyncio
import serial

from hauptbahnhof import Hauptbahnhof

from . import rcswitch

class RupprechtError(Exception):
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
            self.rupprecht = RupprechtInterface("/dev/ttyACM0")
        except serial.SerialException:
            self.rupprecht = RupprechtInterface("/tmp/rupprechtemulator")

        self.rupprecht.subscribe_button(self.button_message)

        self.imposed_ids = {
            'rupprecht-table': rcswitch.Quigg1000(code=1337, subaddr=1,
                                                  rupprecht=self.rupprecht),
            'rupprecht-alarm': rcswitch.Quigg1000(code=1337, subaddr=2,
                                                  rupprecht=self.rupprecht),
            'rupprecht-fan': rcswitch.Quigg1000(code=1337, subaddr=3,
                                                rupprecht=self.rupprecht)
        }

    async def teardown(self):
        await self.hbf.teardown()

    async def command_led(self, source, msg, mqttmsg):
        print("having LED command", msg)
        del source, mqttmsg
        for devid, value in msg.items():
            try:
                if value == 0:
                    await self.imposed_ids[devid].off()
                elif value == 1023:
                    await self.imposed_ids[devid].on()
            except KeyError:
                pass

    async def button_message(self, msg):
        if msg['open'] and not self.space_is_open:
            self.space_is_open = True
            await self.hbf.publish('/haspa/status', {'haspa':'open'})
            await self.rupprecht.text("Status:Open... StuStaNet.e.V....")
        elif not msg['open'] and self.space_is_open:
            self.space_is_open = False
            await self.hbf.publish('/haspa/status', {'haspa':'closed'})
            await self.rupprecht.text("Status:Closed... StuStaNet.e.V....")

class RupprechtInterface:
    def __init__(self, serial_port, baudrate=115200, loop=None):
        self.loop = loop or asyncio.get_event_loop()

        self.button_callbacks = [];

        coro = serial_asyncio.open_serial_connection(loop=self.loop, url=serial_port,
                                                     baudrate=baudrate)
        self.reader, self.writer = self.loop.run_until_complete(coro)

        self.button_queue = asyncio.Queue(loop=loop)
        self.data_queue = asyncio.Queue(loop=loop)
        self.receive_task = self.loop.create_task(self.receive_messages())
        self.callback_task = self.loop.create_task(self.handlecallbacks())


    async def teardown(self):
        try:
            self.receive_task.cancel()
            await self.receive_task
        except asyncio.CancelledError:
            pass

        try:
            self.callback_task.cancel()
            await self.callback_task
        except asyncio.CancelledError:
            pass

    async def receive_messages(self):
        while True:
            try:
                print("Waiting for input:")
                line = await self.reader.readline()
            except serial.SerialException:
                print("SerialException, will terminate")
                self.loop.cancel()
                return
            print("Received: ", line)
            line = line.decode('ascii').strip()
            if str.startswith(line, "BUTTON"):
                print("Button message")
                await self.button_queue.put(line[len("BUTTON"):])
            else:
                print("Into data queue")
                await self.data_queue.put(line)
                print("done")

    async def handlecallbacks(self):
        # filter out the last echo
        #await self.data_queue.get()
        #print("Waiting for message")
        #while "READY" != self.data_queue.get():
        #    pass
        #await self.send_raw("CONFIG ECHO OFF", expect_response=False)
        print("Rupprecht finally there")

        while True:
            button_msg = await self.button_queue.get()
            try:
                buttons = json.loads(button_msg)
            except json.JSONDecodeError:
                print("Invalid json: ", button_msg)
                continue

            for callback in self.button_callbacks:
                try:
                    await callback(buttons)
                except Exception as e:
                    print("Exception while executing callback for", button_msg , e)

    def subscribe_button(self, callback):
        self.button_callbacks.append(callback)

    async def send_raw(self, msg, expect_response=True):
        """
        Send the raw line to the serial stream

        This will wait, until the preceding message has been processed.
        """
        print("Sending RUPPRECHT message: ", msg)
        self.writer.write(msg.encode('ascii'))
        if msg[-1] != "\n":
            self.writer.write(b"\n")
        await self.writer.drain()
        if expect_response:
            return await self.data_queue.get()
        return None

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
