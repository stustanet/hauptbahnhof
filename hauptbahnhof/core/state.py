import asyncio
import itertools
import json
import logging
from typing import Dict, List, Tuple, Set

from .node import create_nodes_from_config, Node
from .translation import Translation
from .config import Config
from .utils import MQTTUpdate, StateUpdate


class State:
    def __init__(self, nodes: List, translation: Translation, logger: logging.Logger):
        self.logger = logger
        self._state = {}

        self.nodes = nodes
        self.translation = translation

        self.ws_update_queue: asyncio.Queue[List[StateUpdate]] = asyncio.Queue()
        self.mqtt_update_queue = asyncio.Queue()

    async def init(self):
        for node in self.nodes:
            await self.mqtt_update_queue.put(
                MQTTUpdate(node.topic, node.state_as_mqtt_message())
            )

    async def _update_node_state(self, topic: str, value: int) -> Tuple[List[StateUpdate], Set[Node]]:
        """
        go through all of our registered nodes, check if the topic matches and update their internal state

        :returns: List of applied state updates, list of changed nodes
        """
        did_update = False
        updated_nodes = set()
        for node in self.nodes:
            valid_node = node.set_state_for_topic(topic, value)
            if valid_node:
                did_update = True
                updated_nodes.add(node)

        updates = [StateUpdate(topic, value)] if did_update else []

        return updates, updated_nodes

    async def update_node_topic(self, topic: str, value: int) -> Tuple[List[StateUpdate], Set[Node]]:
        """
        Process a value input on a topic with translation
        """
        topics = self.translation.translate(topic)
        if not topics:
            # we expect a base topic here
            return await self._update_node_state(topic, value)

        updates: List[Tuple[List[StateUpdate], List[Node]]] = await asyncio.gather(
            *[self._update_node_state(topic, value) for topic in topics]
        )
        state_updates = []
        updated_nodes = set()
        for update in updates:
            # TODO: find a more pythonic way to do this
            state_updates.extend(update[0])
            updated_nodes = updated_nodes.union(update[1])

        return state_updates, updated_nodes

    async def process_updates(self, updates: Dict) -> None:
        # process node updates
        updates: List[Tuple[List[StateUpdate], List[Node]]] = await asyncio.gather(
            *[
                self.update_node_topic(topic, value)
                for topic, value in updates.get("nodes", {}).items()
            ]
        )
        state_updates = []
        updated_nodes = set()
        for update in updates:
            # TODO: find a more pythonic way to do this
            state_updates.extend(update[0])
            updated_nodes = updated_nodes.union(update[1])

        # insert any other state update processing here
        await asyncio.gather(
            self.ws_update_queue.put(state_updates),
            *[self.mqtt_update_queue.put(MQTTUpdate(node.topic, node.state_as_mqtt_message())) for node in updated_nodes]
        )

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
