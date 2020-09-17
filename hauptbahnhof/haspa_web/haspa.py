"""
Display the haspa state as website
"""

import time
import json
from pathlib import Path

from hauptbahnhof import Hauptbahnhof


class HaspaWeb(Hauptbahnhof):
    """
    Recreate the haspa website to represent the current haspa state
    -- This will connect to a remote hauptbahnhof client!
    """

    def __init__(self):
        super().__init__("haspa_web")

        prism_path = Path(__file__).resolve().parent
        self.config["TEMPLATE_PATH"] = prism_path / "templates"
        self.config["OUTPUT_PATH"] = prism_path / "html"

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        self.subscribe("/haspa/status", self.command_state)

    def command_state(self, client, userdata, mqttmsg):
        """ /haspa/status change detected """
        del client, userdata
        message = json.loads(mqttmsg.payload.decode("utf-8"))
        self.logger.info("Received: %s", message)
        if "haspa" in message:
            if message["haspa"] in ["open", "offen", "auf"]:
                self.set_state(True)
            elif message["haspa"] in ["close", "zu", "closed"]:
                self.set_state(False)
            else:
                self.logger.info("Haspa state undetermined: %s", message["haspa"])
        else:
            self.logger.warning("Invalid Message received")

    def set_state(self, is_open):
        """
        Export the current haspa state to the website

        The templates and the update procedure have been designed by pt, I do not want to
        Change any old and glorious routines!
        """
        for template in self.config["TEMPLATE_PATH"].glob("*.tpl"):
            outfile = self.config["OUTPUT_PATH"] / template.stem

            with open(str(template), "r") as orig:
                content = orig.read()
                content = content.replace(
                    "#state#", "offen" if is_open else "geschlossen"
                )
                content = content.replace(
                    "#last_update#", time.strftime("%a, %d %b %Y %H:%M:%S")
                )
                with open(str(outfile), "w") as new:
                    new.write(content)
