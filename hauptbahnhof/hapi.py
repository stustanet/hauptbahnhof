from enum import Enum
import json

class hapi():
    """
    This class defines a simple communication protocol for interaction with the
    Hauptbahnhof.

    All interaction is conducted over a TLS secured channel. All exchanged
    messages must be JSON objects, conforming to the following standard:

        Message :=  REQUEST | RESPONSE

        REQUEST := { 'op' : op.ENTRY, 'data' : data.ENTRY [, 'arg' : DATA ] }
        RESPONSE := { 'state' : state.ENTRY, 'msg' : DATA | ERROR }

            where 'ENTRY' refers to an arbitrary member of the enum
                  'DATA'  refers to arbitrary data
                  'ERROR' refers to a str, containing an error message

    A client may only send messages of type REQUEST, while the Hauptbahnhof will
    reply with a message of type RESPONSE. All other formats are erroneous and
    either cause a RESPONSE with a FAIL state or are simply ignored.
    """

    class op(Enum):
        """
        Operations for use in Hackerspace requests

        Possible values: GET, SET
        """
        GET = 1
        SET = 2

    class data(Enum):
        """
        Data types for use in Hackerspace requests

        Possible values: OPEN, DEVICES, BULB, ALARM
        """
        OPEN = 1
        DEVICES = 2
        BULB = 3
        ALARM = 4

    class state(Enum):
        """
        Status codes for use in Hackerspace responses

        Possible values: SUCCESS, FAIL
        """
        SUCCESS = 1
        FAIL = 2
