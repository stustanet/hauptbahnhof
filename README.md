Mosquitto Hauptbahnhof
---------------------------

A Hackerspace control system based on the mqtt protocol

## Functionality

The mqtt hauptbahnof provides you with the basic functionality to load common system
configuration and connects you to the mqtt server.

The modules used should be independent from each other and only communicate via mqtt
messages, enabling a distribution of the modules across the haspa-of-things.

## Launching

Each module is launched individually from its own submodule and should run independently.
That way if somebody else fucks up, everything still works fine.

You can launch with the following commandline:

```
python3 -m <modulename> --confdir <config directory>
```

To launch a test issue

```
python3 -m <modulename>.test --confdir <config directory>
```

## Configuration

The config directory has to contain at least a `hauptbahnof.conf` with the following
content:

```
host = <mqtt-server>
```

The modules may also load config files - they need to exist as well.


## Create your own module

Just simply copy a module that is already out there and does close to nothing, replace
this nonexistent functionality and you are set to go.

A module should instantiate a Hauptbahnhof object, since this manages all the connection
magic with the mqtt server.

using `Hauptbahnhof.subscribe("topic", callback)` a callback is registered upon a message.
The callback will receive the arguments `(client, messageobj, messageraw)` to process.

using `Hauptbahnhof.publish("topic", object)` to send a json-formatted message to another
Hauptbahnhof (and you yourself will also receive this message)

with `Hauptbahnhof.config("configfile")` you get the config structure of the file
`configfile.conf` from your config directory.

It is recommended to create a test, that tests the functionality of the modules
individually to avoid headaches for your friends and yourself if the beat you up.
