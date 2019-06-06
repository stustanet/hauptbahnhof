import asyncio
import requests
import random

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
        self.hbf.subscribe('/haspa/action', self.command_action)

    async def teardown(self):
        await self.hbf.teardown()

    async def command_status(self, client, message, _):
        """
        React to a status change of the hackerspace - switch the lights, ...
        """
        del client
        try:
            if message['haspa'] in ['open', 'offen', 'auf']:
                await self.hbf.publish('/haspa/power', {
                    'table':1023,
                    'fan':1023,
                    'ledstrip':400,
                })
                await self.hbf.publish('/haspa/music/control', {
                    'play': True
                })
            elif message['haspa'] in ['close', 'zu', 'closed']:
                await self.hbf.publish('/haspa/power', {
                    'table':0,
                    'fan':0,
                    'ledstrip':0,
                    'alarm':0,
                })
                await self.hbf.publish('/haspa/music/control', {
                    'play': False
                })
            else:
                print("Haspa state undetermined: ", message['haspa'])
        except KeyError:
            print("/haspa/status message malformed: ", message)

    async def command_action(self, client, message, _):
        """ Handle actions like alarm or party """
        del client
        print(message)
        if 'action' in message:
            if message['action'] == 'alarm':
                print("Performing alarm...")
                await self.hbf.publish('/haspa/power', {'alarm':1023})
                await asyncio.sleep(2)
                await self.hbf.publish('/haspa/power', {'alarm':0})

            elif message['action'] == 'strobo':
                for i in range(100):
                    await self.hbf.publish('/haspa/power', {
                        'ledstrip-c': 0
                    })
                    await asyncio.sleep(0.05)
                    await self.hbf.publish('/haspa/power', {
                        'ledstrip-c': 1023
                    })
                    await asyncio.sleep(0.03)


            elif message['action'] == 'party':
                await self.hbf.publish('/haspa/power', {
                    'alarm':0,
                    'table':0,
                    'ledstrip': 0
                })
                delay = 0.05

                sounds = [
                    #('56', 3.5), # führer
                    ('97', 4.7), # sonnenschein
                    ('63', 5),   #epische musik
                    ('110', 3.7),#dota
                    ('113', 9),  # skrillex
                ]

                sound = random.choice(sounds)


                if sound[0] == '97':
                    await asyncio.sleep(1)
                    for i in range(0, 300):
                        if i == 100:
                            requests.get("https://bot.stusta.de/set/" + sound[0])

                        await self.hbf.publish('/haspa/power', {
                            'ledstrip-w': i * 10/3
                        })
                        await asyncio.sleep(0.01)
                elif sound[0] == '113':
                    requests.get("https://bot.stusta.de/set/" + sound[0])
                    for i in range(2):
                        await asyncio.sleep(1.5)
                        await self.hbf.publish('/haspa/power', {
                            'ledstrip-c-1': 1023,
                            'ledstrip-c-3': 1023,
                            'alarm':1023
                        })
                        await asyncio.sleep(0.01)
                        await self.hbf.publish('/haspa/power', {
                            'ledstrip-c-1': 0,
                            'ledstrip-c-3': 0
                        })

                        for o in range(40):
                            await self.hbf.publish('/haspa/power', {
                                'ledstrip-c-2': 20 * o,
                                'ledstrip-w-4': 20 * o
                            })
                            await asyncio.sleep(0.01)
                        await self.hbf.publish('/haspa/power', {
                            'Ledstrip-c-2': 0,
                            'ledstrip-w-4': 0
                        })

                        #await asyncio.sleep(1.49)
                        for o in range(20):
                            await self.hbf.publish('/haspa/power', {
                                'ledstrip-c-2': 1023,
                                'ledstrip-w-4': 0
                            })
                            await asyncio.sleep(0.01)
                            await self.hbf.publish('/haspa/power', {
                                'ledstrip-c-2': 0,
                                'ledstrip-w-4': 1023
                            })
                            await asyncio.sleep(0.01)

                else:
                    requests.get("https://bot.stusta.de/set/" + sound[0])
                    for _ in range(int(sound[1]/(delay * 4))):
                        await self.hbf.publish('/haspa/power', {
                            'ledstrip-c-1': 0,
                            'ledstrip-c-2': 1023
                        })
                        print("1->2")
                        await asyncio.sleep(delay)

                        await self.hbf.publish('/haspa/power', {
                            'ledstrip-c-2': 0,
                            'ledstrip-c-3': 1023
                        })
                        print("2->3")
                        await asyncio.sleep(delay)

                        await self.hbf.publish('/haspa/power', {
                            'ledstrip-c-3': 0,
                            'ledstrip-c-4': 1023
                        })
                        print("3->4")
                        await asyncio.sleep(delay)

                        await self.hbf.publish('/haspa/power', {
                            'ledstrip-c-4': 0,
                            'ledstrip-c-1': 1023
                        })
                        print("4->1")
                        await asyncio.sleep(delay)

                        print("round")

                await self.hbf.publish('/haspa/power', {
                    'alarm':0,
                    'table':1023,
                    'ledstrip': 500
                })
