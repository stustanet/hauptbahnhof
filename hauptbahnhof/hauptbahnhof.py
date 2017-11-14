from .hackerspace import Hackerspace

import asyncio
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

    @asyncio.coroutine
    def handle_connection(self, reader, writer):
        """
        Handle incoming connections and dispatch request depending on content.

        This function is called automatically upon a successful TLS connection
        """
        data = yield from reader.read(2048)
        message = data.decode()

        # interpret the incoming request
        resp = yield from self.space.parse_request(message)

        addr = writer.get_extra_info('peername')
        print("{} >>> {}".format(addr, message))

        writer.write(resp.encode())
        print("{} <<< {}".format(addr, resp))
        yield from writer.drain()

        writer.close()

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
            print("Trusted client certificates empty or malformed. Aborting.")
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

        """
        # create listening socket
        bindsocket = socket.socket()
        bindsocket.bind((self.l_addr, int(self.l_port)))
        bindsocket.listen(5)

        s, fromaddr = bindsocket.accept()
        print(fromaddr)

        try:
            stream = context.wrap_socket(s, server_side = True)
        except ssl.SSLError as e:
            print("Connection from {} failed: {}".format(fromaddr,e))
            return None

        print(stream.server_hostname)
        print(stream.getpeercert())
        data = stream.recv(1024)
        print(data)

        bindsocket.close()
        stream.shutdown(socket.SHUT_RDWR)
        stream.close()
        """

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
