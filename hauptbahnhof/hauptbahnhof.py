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

from .hackerspace import Hackerspace

import asyncio
import json
import serial
import ssl

class Hauptbahnhof():
    """
    The 'Hauptbahnhof' provides a centralized interface for secure remote
    interaction with the StuStaNet e.V. Hackerspace.

    A Hauptbahnhof object provides means of requesting status variables from the
    Hackerspace (such as openness, number of connected network devices) and
    requesting functionality (e.g. ringing an alarm in the space).

    Communication is conducted via a TLS secured channel. Only trusted clients
    are able to connect. Authorization is enforced through X509 certificate
    checks. The certificates of all trusted clients need to be copied to the
    server beforehand.
    """

    def __init__(self, l_addr, l_port, s_cert, s_key, client_certs, space):
        """
        Initialize a new Hauptbahnhof and the connections to its subcomponents.

        l_addr:         Address on which the server will listen for connections
        l_port:         Port on which the server will listen for connections
        s_cert:         Server certificate for authentication against clients
        s_key:          Private key of the server certificate
        client_certs:   File containing trusted, concatenated client certs
        space:          Handle to an existing Hackerspace object
        """

        self.l_addr = l_addr
        self.l_port = l_port
        self.s_cert = s_cert
        self.s_key  = s_key
        self.client_certs = client_certs
        self.space = space

        # setup TLS connection context
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=self.s_cert, keyfile=self.s_key)
        # require client authentication for connection
        context.verify_mode = ssl.CERT_REQUIRED

        # specify allowed client certificates
        try:
            context.load_verify_locations(self.client_certs)
        except ssl.SSLError as e:
            print("Trusted client certificates empty or malformed. Aborting.",
                  flush=True)
            return None

        # setup serial connection to arduino (ruprecht)
        self.sconn = serial.Serial('/dev/ttyACM0', 9600)

        # setup asynchronous communication
        self.loop = asyncio.get_event_loop()        # create the loop
        self.loop.add_reader(self.sconn,            # add callback for incoming
                             space.control_panel_cb,# serial data
                             self.sconn)
        coro = asyncio.start_server(self.handle_connection, # start tls server
                                    host = self.l_addr,
                                    port = self.l_port,
                                    ssl = context,
                                    loop = self.loop)

        self.server = self.loop.run_until_complete(coro)    # launch loop

        # Serve requests until Ctrl+C is pressed
        print('Serving on {}'.format(self.server.sockets[0].getsockname()))
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass

        # Close the server
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
        self.loop.close()

    def __del__(self):
        try:
            self.server.close()
            self.loop.run_until_complete(self.server.wait_closed())
            self.loop.close()
        except RuntimeError:
            return

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.server.close()
            self.loop.run_until_complete(self.server.wait_closed())
            self.loop.close()
        except RuntimeError:
            return

    @asyncio.coroutine
    def handle_push_connection(self, conn, service):
        """
        Check an existing tls push channel for incoming data and handle it.
        """
        # Read from channel until unregistration requested or connection dies
        r = conn[0]
        w = conn[1]
        addr = w.get_extra_info('peername')

        while(True):
            # try to read data from the stream
            json_load_failed = False
            data = yield from r.read(2048)

            if (data == b''):
                print("{} xxx {}".format(addr, "Connection reset"))
                break

            message = data.decode()

            print("{} >>> {}".format(addr, message))

            # interpret the received JSON object
            try:
                jsn = json.loads(message)
            except json.decoder.JSONDecodeError as e:
                json_load_failed = True

            if (json_load_failed):
                resp = { 'state' : 'FAIL',
                         'msg'   : "Malformed JSON object: {}".format(message) }
                resp = json.dumps(resp)

                w.write(resp.encode())
                yield

                try:
                    yield from w.drain()
                except ConnectionResetError as e:
                    print("{} xxx {}".format(addr, "Connection reset"))
                    break

                print("{} <<< {}".format(addr, resp))

            else:               # json format correct
                try:
                    if (jsn['op'] == 'UNREGISTER'):
                        resp = { 'state': 'SUCCESS',
                                 'msg'  : "Unregistered from service: "
                                          + "{}".format(service)}
                        resp = json.dumps(resp)

                        w.write(resp.encode())
                        yield

                        try:
                            yield from w.drain()
                        except ConnectionResetError as e:
                            print("{} xxx {}".format(addr, "Connection reset"))
                            break

                        print("{} <<< {}".format(addr, resp))
                        break

                    else:       # other operation than REGISTER
                        resp = yield from self.space.parse_request(jsn)

                        resp = json.dumps(resp)
                        w.write(resp.encode())
                        yield

                        try:
                            yield from w.drain()
                        except ConnectionResetError as e:
                            print("{} xxx {}".format(addr, "Connection reset"))
                            break

                        print("{} <<< {}".format(addr, resp))

                except KeyError as e:
                    resp = { 'state' : 'FAIL',
                             'msg'   : "Unknown operation: {}".format(jsn) }
                    resp = json.dumps(resp)

                    w.write(resp.encode())
                    yield

                    try:
                        yield from w.drain()
                    except ConnectionResetError as e:
                        print("{} xxx {}".format(addr, "Connection reset"))
                        break

                    print("{} <<< {}".format(addr, resp))

        yield from self.unregister_client(conn, service)
        w.close()

    @asyncio.coroutine
    def register_client(self, conn, service):
        """
        Register the given connection for PUSH messages from the specified
        service.
        """
        addr = conn[1].get_extra_info('peername')
        yield from self.space.add_push_target(conn, service)
        print("{} -R- {}".format(addr, service))
        coro = self.handle_push_connection(conn, service)
        self.loop.create_task(coro)

    @asyncio.coroutine
    def unregister_client(self, conn, service):
        """
        Unregister the given connection from PUSH messages for service
        """
        addr = conn[1].get_extra_info('peername')
        yield from self.space.remove_push_target(conn, service)
        print("{} xRx {}".format(addr, service))

    @asyncio.coroutine
    def handle_connection(self, reader, writer):
        """
        Handle incoming connections and dispatch request depending on content.

        This function is called automatically upon a successful TLS connection.
        """
        addr = writer.get_extra_info('peername')
        register_req = False
        json_load_failed = False

        print("{} --- {}".format(addr, "Connected"))

        data = yield from reader.read(2048)

        if (data == b''):
            print("{} xxx {}".format(addr, "Connection reset"))
            writer.close()
            return

        message = data.decode()
        print("{} >>> {}".format(addr, message))

        # interpret the received JSON object
        try:
            jsn = json.loads(message)
        except json.decoder.JSONDecodeError as e:
            json_load_failed = True

        if (json_load_failed):
            resp = { 'state' : 'FAIL',
                     'msg'   : "Malformed JSON object: {}".format(e) }
            resp = json.dumps(resp)
        else:

            # check if the the client wants to register for PUSH messages
            try:
                if (jsn['op'] == 'REGISTER'):
                    service = jsn['data']

                    if (service in self.space.services.keys()):
                        if ('REGISTER' in self.space.services[service]):
                            yield from self.register_client((reader, writer),
                                                            service)
                            register_req = True
                            resp = { 'state': 'SUCCESS',
                                     'msg'  : 'Registered for '
                                              + '{}.'.format(service)}

                        else:
                            resp = { 'state': 'FAIL',
                                     'msg':"Service {}".format(service)
                                       + " can not be registered for."}

                    else:
                        resp = { 'state': 'FAIL',
                                 'msg':"Service {} doesn't".format(service)
                                       + " exist." }

                else:
                    resp = yield from self.space.parse_request(jsn)

            except KeyError as e:
                resp = { 'state' : 'FAIL',
                         'msg'   : "Unknown operation: {}".format(jsn) }


        resp = json.dumps(resp)
        writer.write(resp.encode())
        yield

        try:
            yield from writer.drain()
        except ConnectionResetError as e:
            return

        print("{} <<< {}".format(addr, resp))

        if (not register_req):
            writer.close()

