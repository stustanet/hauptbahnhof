from hapi import hapi

import ast
import asyncio
import json
import subprocess
import socket

class Hackerspace():
    """
    An API for controlling and inspecting the StuStaNet e.V. Hackerspace.

    This class abstracts interaction with the Hackerspace infrastructure.
    This includes supply of status information such as openness, number of
    connected network devices and room temperature. Furthermore it includes
    means to interact with hardware, located in the room. Possible examples are
    audio-visual signals and remote configuration of room characteristics.
    """

    def __init__(self, local_netdev="enp3s0", space_devices=[],
                 space_network='10.150.9.0/24'):
        """
        Initialize a new hackerspace object and the connections to its
        subcomponents.

        local_netdev:   Network device connected to the hackerspace network
        space_devices:  List of MAC-Addresses from stationary HaSpa devices
        space_network:  Range of the Hackerspace local network in CIDR notation
        """

        self.local_netdev = local_netdev
        self.space_devices = space_devices
        self.space_network = space_network
        self.space_open = False

        # Init connection to hackerspace status (database?)

        # Init CAN connection (temp sensors, light, ...)

    def __del__(self):
        print("Hackerspace pwned")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Hackerspace pwned automatically")

    @asyncio.coroutine
    def get_cb(self, jsn):
        """Callback for incoming GET REQUESTS"""

        if (jsn['data'] == hapi.data.OPEN):
            return {'state' : hapi.state.SUCCESS.value, 'msg' : self.space_open}

        elif (jsn['data'] == hapi.data.DEVICES):
            num = yield from self.get_number_of_network_devices()
            return { 'state' : hapi.state.SUCCESS.value, 'msg' : num }

        elif (jsn['data'] == hapi.data.BULB):
            resp = "Can't request the status of BULB"
            return { 'state' : hapi.state.FAIL.value, 'msg' : resp }

        elif (jsn['data'] == hapi.data.ALARM):
            resp = "Can't request the status of ALARM"
            return { 'state' : hapi.state.FAIL.value, 'msg' : resp }

        else:
            return { 'state' : hapi.state.FAIL.value,
                     'msg' : "GET {} operation unknown.".format(jsn['data']) }

    @asyncio.coroutine
    def set_cb(self, jsn):
        """Callback for incoming SET REQUESTS"""

        if (jsn['data'] == hapi.data.OPEN):
            try:
                status = jsn['arg']
            except KeyError as e:
                return {'state' : hapi.state.FAIL.value,
                        'msg' : "No argument given for set operation"}

            if (isinstance(status, bool)):
                self.space_open = status
            else:
                 return {'state' : hapi.state.FAIL.value,
                        'msg' : "Given argument not a boolean value" }

            resp_str = ("Hackerspace now"
                        "{}".format('open' if self.space_open else 'closed'))
            return {'state' : hapi.state.SUCCESS.value,
                    'msg' : resp_str }

        elif (jsn['data'] == hapi.data.DEVICES):
            return { 'state' : hapi.state.FAIL.value,
                     'msg' : "Not a settable parameter" }

        elif (jsn['data'] == hapi.data.BULB):
            state, resp = yield from self.flash_signal()
            if (state):
                state = hapi.state.SUCCESS.value
            else:
                state = hapi.state.FAIL.value
            return { 'state' : state, 'msg' : resp }

        elif (jsn['data'] == hapi.data.ALARM):
            state, resp = self.ring_alarm()
            if (state):
                state = hapi.state.SUCCESS.value
            else:
                state = hapi.state.FAIL.value
            return { 'state' : state, 'msg' : resp }
        else:
            return { 'state' : hapi.state.FAIL.value,
                     'msg' : "GET {} operation unknown.".format(jsn['data']) }

    @asyncio.coroutine
    def parse_request(self, r):
        """ space.parse_request(str) -> str

        Parse the given JSON request and return an appropriate answer
        """
        # Callback definitions
        cb_for = { hapi.op.GET : self.get_cb,
                   hapi.op.SET : self.set_cb }

        resp = ''
        jsn = {'empty' : 'empty'}

        # interpret the retrieved JSON object according to API specifications
        try:
            jsn = json.loads(r)
        except json.decoder.JSONDecodeError as e:
            resp = { 'state' : hapi.state.FAIL.value,
                     'msg'   : "Malformed JSON object: {}".format(e) }

        jsn['op'] = hapi.op(jsn['op'])
        jsn['data'] = hapi.data(jsn['data'])

        # Retrieve the right calback function for the incoming request and exec
        try:
            cb = cb_for[jsn['op']]
            resp = yield from cb(jsn)
        except KeyError as e:
            op = list(jsn.keys())[0]
            resp = { 'state' : hapi.state.FAIL.value,
                     'msg' : "Invalid operation: '{}'".format(op) }

        return json.dumps(resp)

    @asyncio.coroutine
    def get_number_of_network_devices(self):
        """ space.get_number_of_network_devices() -> int

        Return the number of non-stationary, connected network devices.
        """
        proc = subprocess.Popen(['./arp-scan', self.space_network],
                                 stdout=subprocess.PIPE)

        output = proc.communicate()[0].decode('utf8')
        output = output.split()
        proc.terminate()

        dev_list = []

        for line in output:
            if (line.find(':') != -1 and len(line) == 17):
                if (line not in self.space_devices):
                    dev_list.append(line)

        return len(dev_list)

    @asyncio.coroutine
    def ring_alarm(self, duration=5):
        """ Play the alarm sound for the given amount of seconds """
        print("A les armes! (for {} seconds...)".format(duration))
        return True, 42

    @asyncio.coroutine
    def flash_signal(self, duration=5):
        """ Flash the signal lamp for the given amount of seconds """
        print("Now flashing signal lamp...")
        return True, 1337
        #TODO insert communication with wireless socket-outlet here

    def control_panel_cb(s):
        """
        Callback for when data is available on the serial connection to the
        control panel.

        s:      serial.Serial object on which data is available for reading
        """
        try:
            state_string = s.readline().decode()
        except:
            print("Failed to read data from serial connection")
            return

        if 'DEBUG' not in state_string:
            print(state_string)

            if state_string[0] == '0':
                if state_string[1] == '1':
                    self.space_open = True
                    subprocess.call(['mpc', 'play'])
                else:
                    self.space_open = False
                    subprocess.call(['mpc', 'pause'])

            if state_string[0] == '1':
                subprocess.call(['mpc', 'volume', '+5'])
            if state_string[0] == '2':
                subprocess.call(['mpc', 'volume', '-5'])
            if state_string[0] == '3':
                if state_string[1] == '1':
                    subprocess.call(['mpc', 'toggle'])
