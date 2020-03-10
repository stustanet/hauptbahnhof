import asyncio
import json
import time
from json import JSONDecodeError

import requests
import random

from hauptbahnhof import Hauptbahnhof


class Hackerman(Hauptbahnhof):
    """
    Scan the local hackerspace network for new and unknown devices to send back a result
    """

    def __init__(self):
        super().__init__('hackerman')

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        self.subscribe('/haspa/status', self.command_status)
        self.subscribe('/haspa/action', self.command_action)

    def command_status(self, client, userdata, msg,):
        """
        React to a status change of the hackerspace - switch the lights, ...
        """
        try:
            message = json.loads(msg.payload)
        except JSONDecodeError:
            self.log.warn(f'malformed msg on topic {msg.topic}: {msg.payload}')
            return

        if 'haspa' not in message:
            self.log.warn(f"/haspa/status message malformed: {message}")
            return

        if message['haspa'] in ['open', 'offen', 'auf']:
            self.publish('/haspa/licht', 400)
            self.publish('/haspa/music/control', {
                'play': True
            })
        elif message['haspa'] in ['close', 'zu', 'closed']:
            self.publish('/haspa/licht', 0)
            self.publish('/haspa/music/control', {
                'play': False
            })
        else:
            self.log.warn(f"Haspa state undetermined: {message['haspa']}")

    def command_action(self, client, userdata, msg):
        """ Handle actions like alarm or party """
        try:
            message = json.loads(msg.payload)
        except JSONDecodeError:
            self.log.warn(f'malformed msg on topic {msg.topic}: {msg.payload}')
            return

        if 'action' not in message:
            self.log.warn(f'got invalid action msg: {message}')
            return

        if message['action'] == 'alarm':
            self.log.info("Performing alarm...")
            self.publish('/haspa/licht/alarm', 1)
            time.sleep(2)
            self.publish('/haspa/licht/alarm', 0)

        elif message['action'] == 'strobo':
            self.log.info("Performing strobo...")
            for i in range(100):
                self.publish('/haspa/licht/c', 0)
                time.sleep(0.05)
                self.publish('/haspa/licht/c', 1023)
                time.sleep(0.03)

        elif message['action'] == 'party':
            self.log.info("Performing party...")
            self.publish('/haspa/licht', 0)
            self.publish('/haspa/licht/c', 0)
            self.publish('/haspa/licht/w', 0)
            delay = 0.05

            sounds = [
                # ('56', 3.5), # führer
                ('97', 4.7),  # sonnenschein
                ('63', 5),  # epische musik
                ('110', 3.7),  # dota
                ('113', 9),  # skrillex
            ]

            sound = random.choice(sounds)

            if sound[0] == '97':
                await asyncio.sleep(1)
                for i in range(0, 300):
                    if i == 100:
                        requests.get("https://bot.stusta.de/set/" + sound[0])

                    self.publish('/haspa/licht/w', i * 10 / 3)
                    time.sleep(0.01)

            elif sound[0] == '113':
                requests.get("https://bot.stusta.de/set/" + sound[0])
                for i in range(2):
                    time.sleep(1.5)
                    self.publish('/haspa/licht/1/c', 1023)
                    self.publish('/haspa/licht/1/c', 1023)
                    self.publish('/haspa/licht/alarm', 1)

                    time.sleep(0.01)
                    self.publish('/haspa/licht/c', 0)

                    for o in range(40):
                        self.publish('/haspa/licht/c', 20 * o)
                        time.sleep(0.01)

                    self.publish('/haspa/licht/c', 0)

                    # time.sleep(1.49)
                    for o in range(20):
                        self.publish('/haspa/licht/1/c', 1023)
                        self.publish('/haspa/licht/3/c', 0)

                        time.sleep(0.01)

                        self.publish('/haspa/licht/1/c', 0)
                        self.publish('/haspa/licht/3/c', 1023)
                        time.sleep(0.01)

            else:
                requests.get("https://bot.stusta.de/set/" + sound[0])
                for _ in range(int(sound[1] / (delay * 4))):
                    self.publish('/haspa/licht/3/c', 0)
                    self.publish('/haspa/licht/1/c', 1023)
                    time.sleep(delay)

                    self.publish('/haspa/licht/1/c', 0)
                    self.publish('/haspa/licht/4/c', 1023)
                    time.sleep(delay)

                    self.publish('/haspa/licht/4/c', 0)
                    self.publish('/haspa/licht/2/c', 1023)
                    time.sleep(delay)

                    self.publish('/haspa/licht/2/c', 0)
                    self.publish('/haspa/licht/3/c', 1023)
                    time.sleep(delay)

            self.publish('/haspa/licht', 300)
