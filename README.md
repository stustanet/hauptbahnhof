[![Der Hauptbahnhof](hauptbahnhof.jpg)](http://www.bahnhof.de/bahnhof-de/Muenchen_Hbf.html)
==================================================

**Hauptbahnhof**
----------------
The *Hauptbahnhof* provides a centralized interface for secure remote
interaction with the [*StuStaNet e.V.*](http://vereinsanzeiger.stustanet.de/)
Hackerspace. The server provides means of requesting information from the
Hackerspace (such as openness, number of connected network devices, ...) and
triggering Hackerspace Hardware (e.g.  flashing the alarm signal, playing a
sound, ...) from afar. All communication is conducted via TLS encrypted
channels. The server implementation uses *asyncio*.

**Requirements**:

All required python modules are listed in the requirements.txt
file. In order for the network device number scan to work, a local copy of the
*arp-scan* utility with *cap_net_admin* and *cap_net_raw* capabilities needs to
be provided in *$projectroot/hauptbahnhof/*.

The server needs to be configured through the *config.ini* file. This includes
setup of the local network interface as well as serverside and trusted client
x.509 certificates. For hackerspace management, network device name, local space
subnet and stationary devices should be specified.

**Execution**:

After the server has been configured, issue:

```sh
python3 -m hauptbahnhof -c <config_file>
```

The server may also be started and managed via systemd. A systemd service file
template is provided in the projectroot.

**Communication Protocol**:

Communication with the server is conducted via JSON messages, which conform to a
simple, RESTlike protocol. A complete and up-to-date documentation of the
protocol is accessible through the *pythondoc* of the respective modules. An
overview over the protocol is provided in the following:

```
        Message     :=  REQUEST | RESPONSE

        REQUEST     :=  { 'op' : OPERATION, 'data' : SERVICE [, 'arg' : DATA ] }
        RESPONSE    :=  { 'state' : STATE,
                          'msg' : DATA | ERROR
                       [, 'data' : SERVICE ]   }

            where ENTRY refers to an arbitrary member of the enum
                  DATA  refers to arbitrary data
                  ERROR refers to a str, containing an error message

        OPERATION   :=  GET | SET | REGISTER | UNREGISTER
        SERVICE     :=  OPEN | DEVICES | BULB | ALARM | ...
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
```

The currently supported services and their respective operation modes are:

          Target    |           Description           |  Operation Modes
    ----------------|---------------------------------|---------------------
        'OPEN'      | Hackerspace Status              | [GET/SET/REGISTER]
        'DEVICES'   | Amount of NICs in Space network | [GET]
        'BULB'      | Flash the beacon light          | [SET]
        'ALARM'     | Play the alarm sound            | [SET]

**Structure**:

The project is split into two main modules. Main network functionality,
connection management and data dispatching is implemented in the `Hauptbahnhof`
class, while hackerspace management logic and interaction with hardware devices
is implemented in the `Hackerspace` class.


**Cert Magic**

The hauptbahnhof environment is secured using our own CA (on the hauptbahnhof), which only accespts keys stored in a trusted database.

Here is how you create the CA initially:

```
openssl req -x509 -newkey rsa:4096 -sha256 -nodes -keyout hauptbahnhof.key -out hauptbahnhof.crt
```

This generates the CA (the private key) and the public certificate as the root of the certificate chain for all clients.

When one creates a new client, it has to receive a new key (on the client! - private keys must never leave a host!)

```
openssl req -out client.csr -new -newkey rsa:2048 -nodes -keyout client.key
```

Now the client.csr (certificate signing request) is sent over to hauptbahnhof

In order for us to trust it, we have to sign it on hauptbahnhof:

```
openssl x509 -req -in <client.csr> -CA hauptbahnhof.crt  -CAkey hauptbahnhof.key  -CAcreateserial -out <client.crt> -sha256
```

Now - we have a crt! Crts are nice. so we save it to trust it:

```
cat <client.crt> >> trusted.pem
```

Finally - the client has to trust the hauptbahnhof, therefore we copy over the hauptbahnhof.crt (NOT!! the key!)

```
cp hauptbahnhof.crt <client/trusted.pem>
```

Now - happy hauptbahnhofing
