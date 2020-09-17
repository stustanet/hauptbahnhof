from typing import Any


class State:
    def __init__(self, logger):
        self.logger = logger
        self._state = {}

    def get(self, key: str) -> Any:
        return self._state.get(key)

    def set(self, key: str, value: Any):
        self._state[key] = value
