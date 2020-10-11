import argparse
import asyncio
import logging

from .config import Config
from .mqtt import MQTT
from .state import State
from .ws import WebSocket

LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)5s | %(message)s"


def create_parser():
    parser = argparse.ArgumentParser("hauptbahnhof core module")
    parser.add_argument(
        "-c", "--config", type=str, default="/etc/hauptbahnhof/hauptbahnhof.json"
    )

    return parser


async def main():
    args = create_parser().parse_args()

    config = Config.from_file(args.config)
    logging.basicConfig(format=LOG_FORMAT)
    logger = logging.getLogger("core")
    logger.setLevel(logging.DEBUG if config.get("debug", False) else logging.INFO)

    state = State.from_config(config, logger)
    ws = WebSocket(config, state, logger)
    mqtt = MQTT.from_config(config, state, logger)

    await state.init()
    await asyncio.gather(
        ws.start_server(), ws.state_handler(), mqtt.run(), mqtt.handle_state_updates()
    )


if __name__ == "__main__":
    asyncio.run(main())
