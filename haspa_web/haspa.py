"""
Display the haspa state as website
"""

import time
import json
from pathlib import Path

import libconf

from hauptbahnhof import MQTTBahnhofClient

class HaspaWeb:
    """
    Recreate the haspa website to represent the current haspa state
    -- This will connect to a remote hauptbahnhof client!
    """

    def __init__(self):
        with open('/etc/hauptbahnhof/hauptbahnhof.conf') as cfgfile:
            self.config = libconf.load(cfgfile)

        self.hbf = MQTTBahnhofClient(self.config, {
            '/haspa/status': self.command_state
        })

        prism_path = Path(__file__).resolve().parent
        self.config = {}
        self.config['TEMPLATE_PATH'] = prism_path / "templates"
        self.config['OUTPUT_PATH'] = prism_path / "html"

    def command_state(self, client, userdata, mqttmsg):
        """ /haspa/status change detected """
        del client, userdata
        message = json.loads(mqttmsg.payload.decode('utf-8'))
        print("Received:", message)
        if 'haspa' in message:
            if message['haspa'] in ['open', 'offen', 'auf']:
                self.set_state(True)
            elif message['haspa'] in ['close', 'zu', 'closed']:
                self.set_state(False)
            else:
                print("Haspa state undetermined: ", message['haspa'])
        else:
            print("Invalid Message received")

    def set_state(self, is_open):
        """
        Export the current haspa state to the website

        The templates and the update procedure have been designed by pt, I do not want to
        Change any old and glorious routines!
        """
        for template in self.config['TEMPLATE_PATH'].glob('*.tpl'):
            outfile = self.config['OUTPUT_PATH'] / template.stem

            with open(str(template), 'r') as orig:
                content = orig.read()
                content = content.replace('#state#',
                                          "offen" if is_open else "geschlossen")
                content = content.replace('#last_update#',
                                          time.strftime("%a, %d %b %Y %H:%M:%S"))
                with open(str(outfile), 'w') as new:
                    new.write(content)
    def run(self):
        self.hbf.start()
