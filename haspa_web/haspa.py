import asyncio
import time
from pathlib import Path

from hauptbahnhof import Hauptbahnhof

class HaspaWeb:
    """
    Recreate the haspa website to represent the current haspa state
    """

    def __init__(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.hbf = Hauptbahnhof(loop)
        self.hbf.subscribe('/haspa/status', self.command_state)

        prism_path = Path(__file__).resolve().parent
        self.config = {}
        self.config['TEMPLATE_PATH'] = prism_path / "templates"
        self.config['OUTPUT_PATH'] = prism_path / "html"

    async def teardown(self):
        """ Clean it up """
        await self.hbf.teardown()

    async def command_state(self, client, message, _):
        """ After the state has changed, do something! """
        del client
        print(message)
        if 'haspa' in message:
            if message['haspa'] in ['open', 'offen', 'auf']:
                self.set_state(message['haspa'], True)
            elif message['haspa'] in ['close', 'zu', 'closed']:
                self.set_state(message['haspa'], False)
            else:
                print("Haspa state undetermined: ", message['haspa'])

    def set_state(self, state, is_open):
        """
        Export the current haspa state to the website

        The templates and the update procedure have been designed by pt, I do not want to
        Change any old and glorious routines!
        """
        for template in self.config['TEMPLATE_PATH'].glob('*.tpl'):
            print("Updating templates")
            outfile = self.config['OUTPUT_PATH'] / template.stem

            with open(str(template), 'r') as orig:
                content = orig.read()
                content = content.replace('#state#',
                                          "offen" if is_open else "geschlossen")
                content = content.replace('#last_update#',
                                          time.strftime("%a, %d %b %Y %H:%M:%S"))
                with open(str(outfile), 'w') as new:
                    new.write(content)
