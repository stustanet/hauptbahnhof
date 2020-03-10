import json
import sys
import logging
from json import JSONDecodeError
from typing import Dict, Callable, Any, Union, Optional

import paho.mqtt.client as mqtt


class Hauptbahnhof:
    """
    Hauptbahnhof manager with a lot of convenience methods
    """

    def __init__(self, name):
        try:
            idx = sys.argv.index('--confdir')
            self._configbase = sys.argv[idx + 1]
        except (ValueError, KeyError):
            self._configbase = '/etc/hauptbahnhof'

        # find master config
        self.config = {}
        self._load_config("hauptbahnhof")

        self._mqtt = mqtt.Client(client_id=f'hauptbahnhof-{name}')
        self._mqtt.on_message = self._on_message
        self._mqtt.on_connect = self.on_connect

        logformat = '%(name)s | %(levelname)5s | %(message)s'
        logging.basicConfig(format=logformat)
        self.log = logging.getLogger(name)
        self.log.setLevel(logging.DEBUG)
        self._mqtt.enable_logger(self.log)

    def run(self):
        self._connect()
        self._mqtt.loop_forever()

    def _connect(self):
        self.log.debug(f'Trying to connect to broker {self.config["host"]}')
        self._mqtt.connect(self.config['host'])

    def on_connect(self, client, userdata, flags, rc):
        self.log.info(f'Connected to mqqt broker on {self.config["host"]}')

    def _on_message(self, client, userdata, msg):
        try:
            self.on_message(msg)
        except Exception as e:
            self.log.warning(
                msg=f'Invalid message payload received on '
                    f'topic {msg.topic}. Got error {e}')

    def on_message(self, msg) -> None:
        self.log.debug(f'received msg: {msg}')
        raise NotImplementedError()

    def _load_config(self, module: str, not_found_ok=False) -> Dict:
        """
        Load a config from the pile of configs ( usually in /etc/hauptbahnhof/*.conf )
        """
        try:
            with open(f'{self._configbase}/{module}.json', 'r') as f:
                self.config.update(json.load(f))
                return self.config
        except FileNotFoundError as e:
            if not_found_ok:
                return self.config
            raise e

    def subscribe(self, topic: str, callback: Optional[Callable] = None) -> None:
        """
        Subscribe to topic
        """
        self._mqtt.subscribe(topic)
        if callback:
            self._mqtt.message_callback_add(topic, callback)
        self.log.info(f'subscribed to topic {topic}')

    def publish(self, topic: str, msg: Union[str, int, float, Dict]) -> None:
        """
        Publish a message on the given topic
        """
        if isinstance(msg, dict):
            try:
                payload = json.dumps(msg)
            except JSONDecodeError as e:
                self.log.error(
                    msg=f'Got unserializable json dict when trying to'
                        f'send msg to topic {topic}.')
                return
            self._mqtt.publish(topic, payload)
        else:
            self._mqtt.publish(topic, msg)
