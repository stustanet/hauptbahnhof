# Module:
Rupprecht Interaktion [/haspa/led with ids: rupprecht-table, rupprecht-alarm, rupprecht-fan], Sends /haspa/status

* MPD [/haspa/music/\*]
* Device Scanning [/haspa/nsa/\*]
* LED Translater: master of the mapping between light modes and ESP-IDs
* Hackerman: Decide what to do with all these messages
* Actions: [ /haspa/action ]

# Topics

## /haspa/music/control
Haspa start/stop music, Volume control (relative or absolute)

    DATA: {'volume': '+5'}; {'play':False}


## /haspa/music/song
Haspa music control (send mdp-accepted links)

    DATA {'link': 'https://daten.stusta.de/files/pr0n'}
    OPTIONAL "'mode':'append|replace' (default: replace) for playlist management


## /haspa/nsa/scan
ARP Scan for devices, raise /haspa/nsa/result when finished,

    DATA: {'blacklist': ['11:22:33:44:55:66:77:88']}


## /haspa/nsa/result
How many devices where found, that are not blacklisted

    DATA {'count':5}


## /haspa/led (internal use only)
LED Control.

    DATA: {'espID':[0,0,0,0],}


## /haspa/licht
Control the light.

    DATA: 0    # make the hackerspace dark
	DATA: 300  # make the hackerspace normal
	DATA: 1023 # make wolfi blind

more of these haspa/licht topics are configured on knecht in /etc/hauptbahnhof/realms.json

### /haspa/licht/{1,2,3,4}[/{c,w}

set the value of licht 1-4 (enumerated terrace -> werkstatt) cold and warmwhite

DATA is same as /haspa/licht

## /haspa/power/requestinfo
Request all configured lamps with their description

    DATA: {}


## /haspa/power/info
Response for requestinfo

    DATA: {'light':{'desc':'a light'}}

## /haspa/power/status
Request to issue a full power status message to update all clients

    DATA: {}

## /haspa/status
Message that the haspa status has changed, please somebody decide what to do.

    DATA: {'haspa':'open|closed'}


## /haspa/action
Trigger some fun actions like party, alarm, ...

    DATA: {'action':'alarm'}
