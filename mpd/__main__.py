import asyncio
from mpd.mpd import MPD

def main():
    """
    Actually start the shit
    """
    loop = asyncio.get_event_loop()
    mpd = MPD()
    loop.set_debug(True)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(mpd.teardown())

if __name__ == "__main__":
    main()
