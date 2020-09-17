import json
import subprocess
from json import JSONDecodeError

from hauptbahnhof import Hauptbahnhof


class NSA(Hauptbahnhof):
    """
    Scan the local hackerspace network for new and unknown devices to send back a result
    """

    def __init__(self):
        super().__init__("nsa")
        try:
            self._load_config("arplist")
        except FileNotFoundError:
            self.logger.error("no arplist found")
            self.config = {}

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        self.subscribe("/haspa/nsa/scan", self.command_scan)

    def command_scan(self, client, userdata, msg):
        """
        space.get_number_of_network_devices() -> int
        Return the number of non-stationary, connected network devices.
        """
        try:
            message = json.loads(msg.payload)
        except JSONDecodeError:
            self.logger.warning("malformed msg on topic %s: %s", msg.topic, msg.payload)
            return

        known_devices = message.get("blacklist", [])
        known_devices += self.config.get("spacedevices", [])

        # TODO use util/arp-scan
        proc = subprocess.run(
            ["arp-scan", self.config["space_network"]], stdout=subprocess.PIPE,
        )

        output = proc.stdout
        for line in output.decode("utf-8").split("\n"):
            self.logger.debug(line)
        output = output.decode("utf-8").split()

        dev_list = []

        for line in output:
            if line.find(":") != -1 and len(line) == 17:
                if line not in known_devices:
                    dev_list.append(line)

        self.publish("/haspa/nsa/result", {"count": len(dev_list)})
