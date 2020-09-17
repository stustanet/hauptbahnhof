import json
import logging
from pathlib import Path
from typing import Dict


class Config(dict):
    def __init__(self, logger: logging.Logger, cfg: Dict):
        super().__init__(**cfg)
        self.logger = logger

    @classmethod
    def from_file(cls, file_path: Path, logger: logging.Logger):
        if not file_path.exists():
            raise FileNotFoundError(f"could not find config file in {file_path}")

        try:
            with file_path.open("r") as f:
                cfg = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("got json decode error %s when trying to load config file %s", e, file_path)
            raise e

        config = Config(logger=logger, cfg=cfg)

        return config
