#!/usr/bin/python3

from hauptbahnhof.hapi import hapi

import json
import ssl
import socket

def main():

    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.load_cert_chain('./testcert.pem', './testkey.pem')
    context.load_verify_locations('../cert.pem')

    s = socket.socket()
    s.connect(('localhost', 1337))

    try:
        stream = context.wrap_socket(s, server_side = False,
                                     server_hostname='Hauptbahnhof')
    except ssl.SSLError as e:
        print("Connection to target failed: {}".format(e))
        return None

    print(stream.server_hostname)
    print(stream.getpeercert())

    input("Connection established. Press anykey to continue.")

    #jsn = { 'op' : hapi.op.GET.value, 'data' : hapi.data.OPEN.value }
    jsn = { 'op' : hapi.op.SET.value, 'data' : hapi.data.BULB.value }

    count = stream.send(json.dumps(jsn).encode())
    print("Send {} bytes.".format(count))

    resp = stream.recv(1024)
    input("Received: {}.\nPress anykey to exit".format(resp))

    stream.shutdown(socket.SHUT_RDWR)
    stream.close()

if __name__ == '__main__':
    main()
