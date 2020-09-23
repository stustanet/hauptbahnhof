import json
import logging
from typing import Dict, List, TypedDict

from hauptbahnhof.core.config import Config


class Node:
    class JsonRepr(TypedDict):
        type: str
        topic: str
        mappings: Dict[str, int]

    def __init__(self, topic: str, mappings: Dict[str, int]):
        self.topic = topic
        # maps a base topic like /haspa/licht/1/c to an index of this esp
        self.mappings = mappings

        self._state = [0]

    @property
    def state(self):
        return self._state

    def state_as_mqtt_message(self) -> str:
        raise NotImplementedError()

    def set_state_for_topic(self, topic: str, value: int) -> bool:
        """
        Set the internal state for the given mapping topic.
        Will return false if the mapping topic is not known, true if the update was successful.
        """
        if topic not in self.mappings:
            return False

        self._state[self.mappings[topic]] = value
        return True

    def state_for_topic(self, topic: str) -> int:
        if topic not in self.mappings:
            raise KeyError(f"topic {topic} not present in Node mapping")

        if self.mappings[topic] > len(self._state):
            raise IndexError(
                f"topic mapping index {self.mappings[topic]} out of bounds for state of len {len(self._state)}"
            )

        return self._state[self.mappings[topic]]

    def to_dict(self):
        return {mapping: self._state[index] for mapping, index in self.mappings.items()}

    @classmethod
    def from_dict(cls, dct: JsonRepr):
        return cls(topic=dct["topic"], mappings=dct["mappings"])


class DFNode(Node):
    class JsonRepr(TypedDict):
        type: str
        topic: str
        espid: str
        mappings: Dict[str, int]

    def __init__(self, espid: str, topic: str, mappings: Dict[str, int]):
        super().__init__(topic, mappings)
        self.espid = espid

        self._state = [0] * 8

    def state_as_mqtt_message(self) -> str:
        payload = {self.espid: self._state}
        return json.dumps(payload)

    @classmethod
    def from_dict(cls, dct: JsonRepr):
        return cls(topic=dct["topic"], espid=dct["espid"], mappings=dct["mappings"])


class DELock(Node):
    def state_as_mqtt_message(self) -> str:
        return "OFF" if self._state[0] == 0 else "ON"


def create_nodes_from_config(config: Config, logger: logging.Logger) -> List[Node]:
    if "nodes" not in config:
        raise KeyError("error no nodes configured in config")

    nodes = []
    for node_cfg in config["nodes"]:
        if node_cfg.get("type") == "dfnode":
            if (node := DFNode.from_dict(node_cfg)) is not None:
                nodes.append(node)
        elif node_cfg.get("type") == "delock":
            if (node := DELock.from_dict(node_cfg)) is not None:
                nodes.append(node)
        else:
            logger.warning(
                "error, received node config with unknown type %s", node_cfg.get("type")
            )

    return nodes
