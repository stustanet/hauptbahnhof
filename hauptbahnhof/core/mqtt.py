import asyncio
import logging
from typing import List

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_0

from core.config import Config
from core.state import State
from core.utils import MQTTUpdate


class MQTT:
    def __init__(
        self, mqtt_host: str, topics: List[str], state: State, logger: logging.Logger
    ):
        self.logger = logger
        self.host = mqtt_host
        self.state = state

        self.topics = topics

        self._mqtt = MQTTClient()

    async def _connect(self):
        await self._mqtt.connect(self.host)
        self.logger.info("Connected to broker %s", self.host)

    async def handle_message(self, msg):
        self.logger.debug("Received mqtt message on topic %s: %s", msg.topic, msg.data)
        if not msg.data.isnumeric():
            self.logger.warning(
                "Received invalid mqtt payload on topic %s: %s", msg.topic, msg.data
            )
            return

        await self.state.update_topic(msg.topic, int(msg.data))

    async def run(self):
        while True:
            try:
                await self._connect()
                await self._mqtt.subscribe([(topic, QOS_0) for topic in self.topics])
                self.logger.debug("subscribed on topics: %s", self.topics)
                while True:
                    msg = await self._mqtt.deliver_message()
                    await self.handle_message(msg)
            except ClientException as e:
                self.logger.error("Failed when trying to connect to mqtt server: %s", e)
                await asyncio.sleep(10)

    async def handle_state_updates(self):
        while True:
            msg: MQTTUpdate = await self.state.mqtt_update_queue.get()
            await self._mqtt.publish(msg.topic, str(msg.payload).encode())
            self.logger.debug(
                "published mqtt message on topic %s with payload %s",
                msg.topic,
                msg.payload,
            )

    @classmethod
    def from_config(cls, config: Config, state: State, logger: logging.Logger):
        host = config.get("mqtt", {}).get("host")
        port = config.get("mqtt", {}).get("port")
        if not host or not port:
            raise ValueError(f"missing host config for mqtt")

        mqtt = MQTT(
            mqtt_host=f"mqtt://{host}:{port}",
            topics=state.get_mqtt_topics(),
            state=state,
            logger=logger,
        )

        return mqtt
