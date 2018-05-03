import asyncio
from babel.babel import Babel

def main():
    """
    Actually start the shit
    """
    loop = asyncio.get_event_loop()
    babel = Babel()
    loop.set_debug(True)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(babel.teardown())

if __name__ == "__main__":
    main()
