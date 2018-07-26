# Module:
    Rupprecht Interaktion [/haspa/led with ids: rupprecht-table, rupprecht-alarm, rupprecht-fan], Sends /haspa/status
    MPD [/haspa/music/*]
    Device Scanning [/haspa/nsa/*]
    LED Translater: master of the mapping between light modes and ESP-IDs
    Hackerman: Decide what to do with all these messages
    Actions: [ /haspa/action ]

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


## /haspa/power
    Interface to translate commands to common names to /haspa/led. With this interface you have to specify each lamp individually. Commands are aggregated as much as possible
    DATA: {'light':[0-255], 'light2'}
    A value of 0 means "off" a value of "1023" means on, if a light does not support dimming, its state will not change if you send anything else

    Currently Existing power controls:

    * ledstrip-(c|w)(-(1|2|3|4))? = c|w cold/warm white, with optional index, enumerated begininng from the terasse door. If index is ommitted, all leds of that type are addressed.
    * table
    * fan
    * alarm

## /haspa/power/requestinfo
    Request all configured lamps with their description
    DATA: {}


## /haspa/power/info
    Response for requestinfo
    DATA: {'light':{'desc':'a light'}}


## /haspa/status
    Message that the haspa status has changed, please somebody decide what to do.
    DATA: {'haspa':'open|closed'}


##/haspa/action
    Trigger some fun actions like party, alarm, ...
    DATA: {'action':'alarm'}
