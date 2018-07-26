import asyncio

from hauptbahnhof import Hauptbahnhof

class Hackerman:
    """
    Scan the local hackerspace network for new and unknown devices to send back a result
    """

    def __init__(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.hbf = Hauptbahnhof(loop)
        self.hbf.subscribe('/haspa/status', self.command_status)

    async def teardown(self):
        await self.hbf.teardown()

    async def command_status(self, client, message, _):
        """
        React to a status change of the hackerspace - switch the lights, ...
        """
        del client
        try:
            if 'haspa' in message:
                if message['haspa'] in ['open', 'offen', 'auf']:
                    await self.hbf.publish('/haspa/power', {
                        'table':1023,
                        'fan':1023,
                        'ledstrip':400,
                        })
                elif message['haspa'] in ['close', 'zu', 'closed']:
                    await self.hbf.publish('/haspa/power', {
                        'table':0,
                        'fan':0,
                        'ledstrip':0,
                        'alarm':0,
                        })
        except KeyError:
            raise # because - fuck you sender! i will die now, silently.
