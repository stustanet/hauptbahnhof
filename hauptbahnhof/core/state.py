import asyncio
import json
import logging
from typing import Dict, List

from core.babel.node import create_nodes_from_config
from core.babel.translation import Translation
from core.config import Config
from core.utils import MQTTUpdate, StateUpdate


class State:
    def __init__(self, nodes: List, translation: Translation, logger: logging.Logger):
        self.logger = logger
        self._state = {}

        self.nodes = nodes
        self.translation = translation

        self.ws_update_queue = asyncio.Queue()
        self.mqtt_update_queue = asyncio.Queue()

    async def init(self):
        for node in self.nodes:
            await self.mqtt_update_queue.put(
                MQTTUpdate(node.topic, node.state_as_mqtt_message())
            )

    async def _update_node_state(self, topic: str, value: int) -> None:
        update = StateUpdate(topic, value)
        did_update = False
        for node in self.nodes:
            valid_node = node.set_state_for_topic(topic, value)
            if valid_node:
                did_update = True
                await self.mqtt_update_queue.put(
                    MQTTUpdate(node.topic, node.state_as_mqtt_message())
                )

        if did_update:
            await self.ws_update_queue.put(update)

    async def _update_node_topic(self, topic: str, value: int) -> None:
        """
        Process a value input on a topic with translation
        """
        topics = self.translation.translate(topic)
        if not topics:
            # we expect a base topic here
            await self._update_node_state(topic, value)
            return

        await asyncio.gather(
            *[self._update_node_state(topic, value) for topic in topics]
        )

    async def process_updates(self, updates: Dict) -> None:
        # process node updates
        await asyncio.gather(
            *[
                self._update_node_topic(topic, value)
                for topic, value in updates.get("nodes", {}).items()
            ]
        )
        # insert any other state update processing here

    def to_dict(self) -> Dict:
        state_dict = {"nodes": {}, **self._state}
        for node in self.nodes:
            state_dict["nodes"].update(node.to_dict())
        return state_dict

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def get_mqtt_topics(self) -> List[str]:
        topics = self.translation.topics
        for node in self.nodes:
            topics.extend(node.mappings.keys())

        return topics

    @classmethod
    def from_config(cls, config: Config, logger: logging.Logger) -> "State":
        state = cls(
            nodes=create_nodes_from_config(config, logger),
            translation=Translation.from_config(config),
            logger=logger,
        )

        return state
