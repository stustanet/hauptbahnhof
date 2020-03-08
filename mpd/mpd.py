import json
import re
import subprocess
from json import JSONDecodeError

from hauptbahnhof import Hauptbahnhof


class MPD(Hauptbahnhof):
    """
    Implement Interfacing to a locally running mpd server
    """

    def __init__(self):
        super().__init__('mpd')

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        self.subscribe('/haspa/music/control', self.command_control)
        self.subscribe('/haspa/music/song', self.command_song)

    def command_control(self, client, userdata, msg):
        try:
            message = json.loads(msg.payload)
        except JSONDecodeError:
            self.log.warn(f'malformed msg on topic {msg.topic}: {msg.payload}')
            return

        if 'play' in message:
            if message['play']:
                self.log.info("Starting music")
                subprocess.call(['mpc', 'play'])
            else:
                self.log.info("Stopping music")
                subprocess.call(['mpc', 'pause'])
        if 'volume' in message:
            p = re.compile(r'^[-+]?[0-9]{3}$')
            if p.match(message['volume']):
                self.log.info("adjusting volume")
                subprocess.call(['mpc', 'volume', message['volume']])
            else:
                self.log.info("Will not parse volume: %s", message['volume'])

    async def command_song(self, client, userdata, msg):
        pass
