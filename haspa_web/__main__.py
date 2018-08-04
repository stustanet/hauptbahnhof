import asyncio
from haspa_web.haspa import HaspaWeb

def main():
    """
    Actually start the shit
    """
    loop = asyncio.get_event_loop()
    haspaweb = HaspaWeb()
    loop.set_debug(True)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(haspaweb.teardown())

if __name__ == "__main__":
    main()
