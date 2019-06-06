import asyncio
import subprocess
import re

from hauptbahnhof import Hauptbahnhof

class MPD:
    """
    Implement Interfacing to a locally running mpd server
    """

    def __init__(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.hbf = Hauptbahnhof("mpd", loop)
        self.hbf.subscribe('/haspa/music/control', self.command_control)
        self.hbf.subscribe('/haspa/music/song', self.command_song)


    async def teardown(self):
        await self.hbf.teardown()

    async def command_control(self, client, message, _):
        if 'play' in message:
            if message['play']:
                self.hbf.log.info("Starting music")
                subprocess.call(['mpc', 'play'])
            else:
                self.hbf.log.info("Stopping music")
                subprocess.call(['mpc', 'pause'])
        if 'volume' in message:
            p = re.compile(r'^[-+]?[0-9]{3}$')
            if p.match(message['volume']):
                self.hbf.log.info("adjusting volume")
                subprocess.call(['mpc', 'volume', message['volume']])
            else:
                self.hbf.log.info("Will not parse volume: %s", message['volume'])

    async def command_song(self, client, message, _):
        pass
