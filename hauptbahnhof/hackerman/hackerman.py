import json
import time
from json import JSONDecodeError

import requests
import random

from hauptbahnhof import Hauptbahnhof, logger


class Hackerman(Hauptbahnhof):
    """
    Scan the local hackerspace network for new and unknown devices to send back a result
    """

    def __init__(self):
        super().__init__("hackerman")

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        self.subscribe("/haspa/status", self.command_status)
        self.subscribe("/haspa/action", self.command_action)

    def command_status(
        self,
        client,
        userdata,
        msg,
    ):
        """
        React to a status change of the hackerspace - switch the lights, ...
        """
        try:
            message = json.loads(msg.payload)
        except JSONDecodeError:
            logger.warning(f"malformed msg on topic {msg.topic}: {msg.payload}")
            return

        if "haspa" not in message:
            logger.warning(f"/haspa/status message malformed: {message}")
            return

        if message["haspa"] in ["open", "offen", "auf"]:
            # set the best of all possible light settings
            self.publish("/haspa/licht/w", 400)
            self.publish("/haspa/licht/c", 100)
            self.publish("/haspa/licht/tisch", 1)
            self.publish("/haspa/tisch/r", 160)
            self.publish("/haspa/tisch/g", 100)
            self.publish("/haspa/tisch/b", 70)
            self.publish("/haspa/tisch/w", 90)

            self.publish("/haspa/music/control", {"play": True})
        elif message["haspa"] in ["close", "zu", "closed"]:
            self.publish("/haspa/licht", 0)
            self.publish("/haspa/music/control", {"play": False})
        else:
            logger.warning("Haspa state undetermined: %s", {message["haspa"]})

    def command_action(self, client, userdata, msg):
        """ Handle actions like alarm or party """
        try:
            message = json.loads(msg.payload)
        except JSONDecodeError:
            logger.warning(f"malformed msg on topic {msg.topic}: {msg.payload}")
            return

        if "action" not in message:
            logger.warning(f"got invalid action msg: {message}")
            return

        if message["action"] == "alarm":
            logger.info("Performing alarm...")
            self.publish("/haspa/licht/alarm", 1)
            time.sleep(2)
            self.publish("/haspa/licht/alarm", 0)

        elif message["action"] == "strobo":
            logger.info("Performing strobo...")
            for i in range(100):
                self.publish("/haspa/licht/c", 0)
                time.sleep(0.05)
                self.publish("/haspa/licht/c", 1023)
                time.sleep(0.03)

        elif message["action"] == "party":
            logger.info("Performing party...")
            self.publish("/haspa/licht", 0)
            self.publish("/haspa/licht/c", 0)
            self.publish("/haspa/licht/w", 0)
            delay = 0.05

            sounds = [
                # ('56', 3.5), # führer
                ("97", 4.7),  # sonnenschein
                ("63", 5),  # epische musik
                ("110", 3.7),  # dota
                ("113", 9),  # skrillex
            ]

            sound = random.choice(sounds)

            if sound[0] == "97":
                time.sleep(1)
                for i in range(0, 300):
                    if i == 100:
                        requests.get("https://bot.stusta.de/set/" + sound[0])

                    self.publish("/haspa/licht/w", i * 10 / 3)
                    time.sleep(0.01)

            elif sound[0] == "113":
                requests.get("https://bot.stusta.de/set/" + sound[0])
                for i in range(2):
                    time.sleep(1.5)
                    self.publish("/haspa/licht/1/c", 1023)
                    self.publish("/haspa/licht/1/c", 1023)
                    self.publish("/haspa/licht/alarm", 1)

                    time.sleep(0.01)
                    self.publish("/haspa/licht/c", 0)

                    for o in range(40):
                        self.publish("/haspa/licht/c", 20 * o)
                        time.sleep(0.01)

                    self.publish("/haspa/licht/c", 0)

                    # time.sleep(1.49)
                    for o in range(20):
                        self.publish("/haspa/licht/1/c", 1023)
                        self.publish("/haspa/licht/3/c", 0)

                        time.sleep(0.01)

                        self.publish("/haspa/licht/1/c", 0)
                        self.publish("/haspa/licht/3/c", 1023)
                        time.sleep(0.01)

            else:
                requests.get("https://bot.stusta.de/set/" + sound[0])
                for _ in range(int(sound[1] / (delay * 4))):
                    self.publish("/haspa/licht/3/c", 0)
                    self.publish("/haspa/licht/1/c", 1023)
                    time.sleep(delay)

                    self.publish("/haspa/licht/1/c", 0)
                    self.publish("/haspa/licht/4/c", 1023)
                    time.sleep(delay)

                    self.publish("/haspa/licht/4/c", 0)
                    self.publish("/haspa/licht/2/c", 1023)
                    time.sleep(delay)

                    self.publish("/haspa/licht/2/c", 0)
                    self.publish("/haspa/licht/3/c", 1023)
                    time.sleep(delay)

            self.publish("/haspa/licht", 300)
