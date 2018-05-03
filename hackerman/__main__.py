import asyncio

from hackerman.hackerman import Hackerman

def main():
    """
    Actually start the shit
    """
    loop = asyncio.get_event_loop()
    hackerman = Hackerman(loop=loop)
    loop.set_debug(True)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(hackerman.teardown())

if __name__ == "__main__":
    main()
