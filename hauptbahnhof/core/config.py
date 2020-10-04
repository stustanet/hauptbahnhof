import json
from pathlib import Path
from typing import Dict, Union, Optional


class Config(dict):
    def __init__(self, cfg: Optional[Dict] = None):
        cfg = cfg or {}
        super().__init__(**cfg)

    @classmethod
    def from_file(cls, file_path: Union[str, Path]):
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"could not find config file in {file_path}")

        try:
            with file_path.open("r") as f:
                cfg = json.load(f)
        except json.JSONDecodeError as e:
            raise e

        config = Config(cfg=cfg)

        return config
