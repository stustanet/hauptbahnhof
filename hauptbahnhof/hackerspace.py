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

    This class furthermore defines a simple communication protocol for
    interaction through the Hauptbahnhof.

    All interaction is conducted over a TLS secured channel, managed by the
    Hauptbahnhof. All exchanged messages must be JSON objects, conforming to the
    following standard:

        Message     :=  REQUEST | RESPONSE

        REQUEST     :=  { 'op' : OPERATION, 'data' : TARGET [, 'arg' : DATA ] }
        RESPONSE    :=  { 'state' : STATE,
                          'msg' : DATA | ERROR
                          [, 'data' : TARGET }

            where ENTRY refers to an arbitrary member of the enum
                  DATA  refers to arbitrary data
                  ERROR refers to a str, containing an error message

        OPERATION   :=  GET | SET | REGISTER | UNREGISTER
        TARGET      :=  OPEN | DEVICES | BULB | ALARM
        STATE       :=  SUCCESS | FAIL | PUSH

            where GET       : Request the value/data for the given TARGET
                  SET       : Set the value/data for the given TARGET
                  REGISTER  : Register the client for PUSH messages on change of
                              value of TARGET
                  UNREGISTER: Unregister the client from a PUSH message
                              abonnement for TARGET

                  'SUCCESS' : Denotes a successful request. The 'msg' field now
                              holds the requested data
                  'FAIL'    : Denotes a failed request. The 'msg' field now
                              holds an error message, describing what went wrong
                  'PUSH'    : The server pushed a message on behalf of a PUSH
                              abonnement for TARGET. The 'msg' field now holds
                              the value data.

    The currently supported values/modules and respective operation modes are:

          Target    |           Description           |  Operation Modes
    ----------------+---------------------------------+---------------------
        'OPEN'      | Hackerspace Status              | [GET/SET/REGISTER]
        'DEVICES'   | Amount of NICs in Space network | [GET]
        'BULB'      | Flash the beacon light          | [SET]
        'ALARM'     | Play the alarm sound            | [SET]

    A client may only send messages of type REQUEST, while the Hauptbahnhof will
    reply with a message of type RESPONSE. All other formats are erroneous and
    either cause a RESPONSE with a FAIL state or are simply ignored.
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
        # Format: {'OPEN': [writer_obj1, writer_obj2,...], ...}
        self.push_devices = {}

    def __del__(self):
        print("Hackerspace pwned")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Hackerspace pwned automatically")

    @asyncio.coroutine
    def get_cb(self, jsn):
        """Callback for incoming GET REQUESTS"""

        if (jsn['data'] == 'OPEN'):
            return {'state' : 'SUCCESS', 'msg' : self.space_open}

        elif (jsn['data'] == 'DEVICES'):
            num = yield from self.get_number_of_network_devices()
            return { 'state' : 'SUCCESS', 'msg' : num }

        elif (jsn['data'] == 'BULB'):
            resp = "Can't request the status of BULB"
            return { 'state' : 'FAIL', 'msg' : resp }

        elif (jsn['data'] == 'ALARM'):
            resp = "Can't request the status of ALARM"
            return { 'state' : 'FAIL', 'msg' : resp }

        else:
            return { 'state' : 'FAIL',
                     'msg' : "GET {} operation unknown.".format(jsn['data']) }

    @asyncio.coroutine
    def set_cb(self, jsn):
        """Callback for incoming SET REQUESTS"""

        if (jsn['data'] == 'OPEN'):
            try:
                status = jsn['arg']
            except KeyError as e:
                return {'state' : 'FAIL',
                        'msg' : "No argument given for set operation"}

            if (isinstance(status, bool)):
                self.space_open = status
            else:
                 return {'state' : 'FAIL',
                        'msg' : "Given argument not a boolean value" }

            resp_str = ("Hackerspace now"
                        "{}".format('open' if self.space_open else 'closed'))
            return {'state' : 'SUCCESS',
                    'msg' : resp_str }

        elif (jsn['data'] == 'DEVICES'):
            return { 'state' : 'FAIL',
                     'msg' : "Not a settable parameter" }

        elif (jsn['data'] == 'BULB'):
            state, resp = yield from self.flash_signal()
            if (state):
                state = 'SUCCESS'
            else:
                state = 'FAIL'
            return { 'state' : state, 'msg' : resp }

        elif (jsn['data'] == 'ALARM'):
            state, resp = self.ring_alarm()
            if (state):
                state = 'SUCCESS'
            else:
                state = 'FAIL'
            return { 'state' : state, 'msg' : resp }
        else:
            return { 'state' : 'FAIL',
                     'msg' : "GET {} operation unknown.".format(jsn['data']) }

    @asyncio.coroutine
    def parse_request(self, r):
        """ space.parse_request(str) -> str

        Parse the given JSON request and return an appropriate answer
        """
        # Callback definitions
        cb_for = { 'GET' : self.get_cb,
                   'SET' : self.set_cb }

        resp = ''
        jsn = {'empty' : 'empty'}

        # interpret the retrieved JSON object according to API specifications
        try:
            jsn = json.loads(r)
        except json.decoder.JSONDecodeError as e:
            resp = { 'state' : 'FAIL',
                     'msg'   : "Malformed JSON object: {}".format(e) }

        # Retrieve the right calback function for the incoming request and exec
        try:
            cb = cb_for[jsn['op']]
            resp = yield from cb(jsn)
        except KeyError as e:
            op = list(jsn.keys())[0]
            resp = { 'state' : 'FAIL',
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

    def control_panel_cb(self, s):
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
