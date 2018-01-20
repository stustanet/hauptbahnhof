"""
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import ast
import asyncio
import json
import subprocess
import socket

import haspalight
import rupprecht

# Temporary Workaround
import sleekxmpp
ROOM_TOPIC = "Hackerspace: {} | StuStaNet e. V. public chatroom | 42"

# This is only a temporary workaround, to keep the hackerspace
# status exported, until all services communicate directly
# with the hauptbahnhof
class MUCBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, room, nick, message):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = room
        self.nick = nick
        self.message= message

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler("session_start", self.start)


    def start(self, event):
        print("start function called")
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        wait=True)

        self.send_message(self.room,
                          mbody='',
                          msubject=ROOM_TOPIC.format(self.message),
                          mtype='groupchat')

        self.disconnect(wait=True)

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

        REQUEST     :=  { 'op' : OPERATION, 'data' : SERVICE [, 'arg' : DATA ] }
        RESPONSE    :=  { 'state' : STATE,
                          'msg' : DATA | ERROR
                          [, 'data' : SERVICE ] }

            where ENTRY refers to an arbitrary member of the enum
                  DATA  refers to arbitrary data
                  ERROR refers to a str, containing an error message

        OPERATION   :=  GET | SET | REGISTER | UNREGISTER
        SERVICE     :=  OPEN | DEVICES | BULB | ALARM
        STATE       :=  SUCCESS | FAIL | PUSH

            where GET       : Request the value/data for the given SERVICE
                  SET       : Set the value/data for the given SERVICE
                  REGISTER  : Register the client for PUSH messages on change of
                              value of SERVICE
                  UNREGISTER: Unregister the client from a PUSH message
                              abonnement for SERVICE

                  'SUCCESS' : Denotes a successful request. The 'msg' field now
                              holds the requested data
                  'FAIL'    : Denotes a failed request. The 'msg' field now
                              holds an error message, describing what went wrong
                  'PUSH'    : The server pushed a message on behalf of a PUSH
                              abonnement for SERVICE. The 'msg' field now holds
                              the value data.

    The currently supported values/modules and respective operation modes are:

          Target    |           Description           |  Operation Modes
    ----------------+---------------------------------+---------------------
        'OPEN'      | Hackerspace Status              | [GET/SET/REGISTER]
        'DEVICES'   | Amount of NICs in Space network | [GET]
        'BULB'      | Flash the beacon light          | [SET]
        'ALARM'     | Play the alarm sound            | [SET]
        'FAN'       | Control the fan                 | [SET]

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

        self.services = {'OPEN'     : ['GET','SET','REGISTER'],
                         'DEVICES'  : ['GET'],
                         'BULB'     : ['SET'],
                         'ALARM'    : ['SET'],
                         'FAN'      : ['SET']}

        self.local_netdev = local_netdev
        self.space_devices = space_devices
        self.space_network = space_network
        self.space_open = False
        # Format: {'OPEN': [(reader0, writer0), (reader1, writer1),...], ...}
        self.push_devices = {}
        self.push_device_lock = asyncio.Lock()

        # For remote controlling the arduino: initialize the rupprecht interface
        self.rupprecht = rupprecht.RupprechtInterface("/dev/ttyUSB0")
        self.rupprecht.subscribe_button(self.rupprecht_button_msg)

        self.light = rcswitch.Quigg1000(code=1337, subaddr=1, rupprecht=self.rupprecht)
        self.alarm = rcswitch.Quigg1000(code=1337, subaddr=2, rupprecht=self.rupprecht)
        self.fan = rcswitch.Quigg1000(code=1337, subaddr=3, rupprecht=self.rupprecht)

    def __del__(self):
        print("Hackerspace pwned", flush=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Hackerspace pwned automatically", flush=True)

    @asyncio.coroutine
    def push_changes(self, service, value):
        """
        Push value of service to all registered targets
        """
        try:
            if (self.push_devices != {}):
                targets = self.push_devices[service]
            else:
                return

        except KeyError as e:
            print("Failed to retrieve PUSH targets for service"
                  + " {}".format(service))
            return

        msg = { "state" : "PUSH",
                "data"  : service,
                "msg"   : value }
        msg = json.dumps(msg)

        for t in targets:

            addr = t[1].get_extra_info('peername')
            t[1].write(msg.encode())
            yield

            try:
                yield from t[1].drain()
            except ConnectionResetError as e:
                self.remove_push_target(t, service)
                print("{} xPx {}:{}".format(addr, service, value)
                      + "Not reachable. Unregistering.")
                continue

            print("{} <P< {}:{}".format(addr, service, value))

    @asyncio.coroutine
    def add_push_target(self, conn, service):
        """
        Mutually exclusive add of a PUSH target to the recipient list
        """
        yield from self.push_device_lock.acquire()
        try:
            cur = self.push_devices[service]
        except KeyError as e:
            cur = []
        cur.append(conn)
        self.push_devices[service] = cur
        self.push_device_lock.release()

    @asyncio.coroutine
    def remove_push_target(self, conn, service):
        """
        Mutually exclusive remove of a PUSH target from the recipient list
        """
        yield from self.push_device_lock.acquire()
        try:
            cur = self.push_devices[service]
        except KeyError as e:
            print("Service entry {} doesn't exist in dict.".format(service),
                  "Nothing to remove.")
            self.push_device_lock.release()
            return

        try:
            cur.remove(conn)
        except ValueError as e:
            print("Requested removal of non-existant target {}".format(conn))
        self.push_devices[service] = cur
        self.push_device_lock.release()

    @asyncio.coroutine
    def get_cb(self, jsn):
        """Callback for incoming GET REQUESTS"""

        try:
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

            elif (jsn['data'] == 'FAN'):
                resp = "Can't request the status of " + jsn['data']
                return { 'state' : 'FAIL', 'msg' : resp }

            else:
                return { 'state' : 'FAIL',
                         'msg' :"GET {} operation unknown.".format(jsn['data'])}
        except KeyError as e:
            return { 'state' : 'FAIL',
                     'msg'   : "No data parameter: {}".format(jsn) }

    @asyncio.coroutine
    def set_cb(self, jsn):
        """Callback for incoming SET REQUESTS"""
        try:
            if (jsn['data'] == 'OPEN'):
                try:
                    status = jsn['arg']
                except KeyError as e:
                    return {'state' : 'FAIL',
                            'msg' : "No argument given for set operation"}
                if (isinstance(status, bool)):
                    self.space_open = status
                    if status:
                        yield from self.light.light.on()
                    else:
                        yield from self.light.light.off()
                else:
                     return {'state' : 'FAIL',
                            'msg' : "Given argument not a boolean value" }

                yield from self.push_changes('OPEN', self.space_open)

                resp_str =("Hackerspace now "
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

            elif (jsn['data'] == 'FAN'):
                if (jsn['arg'] in ['on', 'start', '1', 1]):
                    yield from self.light.fan.on()
                    return { 'state': 'SUCCESS', 'msg':'FAN is on' }
                elif (jsn['arg'] in ['off', 'stop', '0', 0]):
                    yield from self.light.fan.off()
                    return { 'state': 'SUCCESS', 'msg':'FAN is off' }
                else:
                    return { 'state' : 'FAIL', 'msg' : 'unknown state flag {}'.format(jsn['arg']) }

            else:
                return { 'state' : 'FAIL',
                         'msg': "SET {} operation unknown.".format(jsn['data'])}

        except KeyError as e:
            return { 'state' : 'FAIL',
                     'msg'   : "No data parameter: {}".format(jsn) }

    @asyncio.coroutine
    def parse_request(self, jsn):
        """ space.parse_request(str) -> str

        Parse the given JSON request and return an appropriate answer
        """
        # Callback definitions
        cb_for = { 'GET' : self.get_cb,
                   'SET' : self.set_cb }

        resp = ''

        # Retrieve the right callback function for the incoming request and exec
        try:
            cb = cb_for[jsn['op']]
            resp = yield from cb(jsn)
        except KeyError as e:
            op = list(jsn.keys())[0]
            resp = { 'state' : 'FAIL',
                     'msg' : "Invalid operation: '{}'".format(op) }

        return resp

    @asyncio.coroutine
    def get_number_of_network_devices(self):
        """ space.get_number_of_network_devices() -> int

        Return the number of non-stationary, connected network devices.
        """
        proc = subprocess.Popen(['./hauptbahnhof/arp-scan', self.space_network],
                                 stdout=subprocess.PIPE)

        output = proc.communicate()[0].decode('utf8')
        print("\n" + output)
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
        yield from self.light.alarm.on()
        yield from asyncio.wait(duration)
        yield from self.light.alarm.off()
        return True, 42

    @asyncio.coroutine
    def flash_signal(self, duration=5):
        """ Flash the signal lamp for the given amount of seconds """
        print("Now flashing signal lamp...")
        yield from self.light.light.on()
        yield from asyncio.wait(duration)
        yield from self.light.light.off()

        return True, 1337
        #TODO insert communication with wireless socket-outlet here

    # Workaround function, exporting Hackerspace status to Jabber Channel
    def send_state(self, message):
        print("Trying to send state", message)
        # login every time the state changes
        jid = 'erbsensuppe@jabber.ccc.de'
        password = 'erbsensuppe'
        room = 'admins@conference.jabber.stusta.mhn.de'
        nick = 'knechtbot'

        # Setup the MUCBot and register plugins. Note that while plugins may
        # have interdependencies, the order in which you register them does
        # not matter.
        xmpp = MUCBot(jid, password, room, nick, message)
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0045') # Multi-User Chat
        xmpp.register_plugin('xep_0199') # XMPP Ping

        print("Trying to connect")
        if xmpp.connect():
            # block until message is send (sic!)
            xmpp.process(block=False)
        else:
            print("Unable to connect.")


    @asyncio.coroutine
    def rupprecht_button_msg(msg):
        if msg['open']:
            self.space_open = True
            yield from self.push_changes('OPEN', self.space_open)
            subprocess.call(['mpc', 'play'])
            yield from self.light.on()
            yield from self.alarm.off()
        else:
            self.space_open = False
            yield from self.push_changes('OPEN', self.space_open)
            subprocess.call(['mpc', 'pause'])
            yield from self.light.off()
            yield from self.alarm.off();
            yield from self.fan.off();

        # TODO: Add volup voldown playpause !! POLARISATION !!

        if msg['volup']:
            subprocess.call(['mpc', 'volume', '+5'])

        if msg['voldown']:
            subprocess.call(['mpc', 'volume', '-5'])

        if msg['playpause'] and msg['open']:
            subprocess.call(['mpc', 'toggle'])

