from typing import List, Dict, Set, Optional

from hauptbahnhof.core import Config

MAX_RECURSION_DEPTH = 10


class RecursionDepthExceeded(Exception):
    pass


class Translation:
    def __init__(self, mappings: Dict[str, List[str]]):
        self._mappings = mappings

    def _translate(self, topic, depth=0) -> Set[str]:
        if topic not in self._mappings:
            return {topic}

        if depth < MAX_RECURSION_DEPTH:
            return set().union(
                *[self._translate(t, depth + 1) for t in self._mappings[topic]]
            )
        else:
            raise RecursionDepthExceeded()

    def translate(self, topic) -> Optional[Set[str]]:
        if topic not in self._mappings:
            return None

        return self._translate(topic)

    @property
    def topics(self) -> List[str]:
        topics = set()
        for mapping, mapped in self._mappings.items():
            topics.add(mapping)
            topics.update(set(mapped))
        return list(topics)

    @classmethod
    def from_config(cls, config: Config) -> "Translation":
        return cls(config.get("translation", {}))
