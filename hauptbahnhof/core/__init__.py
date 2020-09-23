import argparse
import json
import logging
import time
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, Callable, Union, Optional

from hauptbahnhof.core.config import Config

import paho.mqtt.client as mqtt

ERROR_MESSAGES = {
    0: "Connection successful",
    1: "Incorrect Protocol Version",
    2: "Invalid client identifier",
    3: "Server unavailable",
    4: "Bad username or password",
    5: "Not authorized",
}
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)5s | %(message)s"


class HauptbahnhofModule:
    """
    Hauptbahnhof manager with a lot of convenience methods
    """

    def __init__(self, name):
        self.name = name
        args = self.create_parser().parse_args()

        self._config_base_dir = args.config_dir

        # find master config
        self.config = Config()
        self._load_config("hauptbahnhof")

        self._mqtt = mqtt.Client(client_id=f"hauptbahnhof-{self.name}")
        self._mqtt.on_message = self._on_message
        self._mqtt.on_connect = self.on_connect

        logging.basicConfig(format=LOG_FORMAT)
        self.logger: logging.Logger = logging.getLogger(self.name)
        if self.config.get("debug", False):
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self._mqtt.enable_logger(self.logger)

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(f"Hauptbahnhof {self.name}")
        parser.add_argument("--config-dir", type=str, default="/etc/hauptbahnhof")

        return parser

    def run(self):
        while True:
            try:
                self._connect()
                break
            except ConnectionRefusedError as e:
                self.logger.error(
                    "Failed when trying initial connect to mqtt server: %s", e
                )
                time.sleep(5)

        self._mqtt.loop_forever()

    def _connect(self):
        self.logger.debug("Trying to connect to broker %s", self.config["host"])
        self._mqtt.connect(self.config["host"])

    def on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            if rc in ERROR_MESSAGES:
                msg = ERROR_MESSAGES[rc]
            else:
                msg = "Unknown error occured: " + rc
            self.logger.error(msg)
        self.logger.info("Connected to mqqt broker on %s", self.config["host"])

    def _on_message(self, client, userdata, msg):
        try:
            self.on_message(msg)
        except Exception as e:
            self.logger.warning(
                "Invalid message payload received on topic %s. Got error %s",
                msg.topic,
                e,
            )

    def on_message(self, msg) -> None:
        self.logger.debug("received msg: %s", msg)
        raise NotImplementedError()

    def _load_config(self, module: str, not_found_ok=False) -> Dict:
        """
        Load a config from the pile of configs ( usually in /etc/hauptbahnhof/*.conf )
        """
        file_path = Path(f"{self._config_base_dir}/{module}.json")
        if file_path.exists():
            with open(file_path, "r") as f:
                self.config.update(json.load(f))
                return self.config

        if not_found_ok:
            return self.config

        raise FileNotFoundError(f"Did not find config file {file_path}")

    def subscribe(self, topic: str, callback: Optional[Callable] = None) -> None:
        """
        Subscribe to topic
        """
        self._mqtt.subscribe(topic)
        if callback:
            self._mqtt.message_callback_add(topic, callback)
        self.logger.info("subscribed to topic %s", topic)

    def publish(self, topic: str, msg: Union[str, int, float, Dict]) -> None:
        """
        Publish a message on the given topic
        """
        if isinstance(msg, dict):
            try:
                payload = json.dumps(msg)
            except JSONDecodeError:
                self.logger.error(
                    "Got unserializable json dict when trying to"
                    "send msg to topic %s.",
                    topic,
                )
                return
            self._mqtt.publish(topic, payload)
        else:
            self._mqtt.publish(topic, msg)
