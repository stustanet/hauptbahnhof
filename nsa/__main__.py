import asyncio
from nsa.nsa import NSA

def main():
    """
    Actually start the shit
    """
    loop = asyncio.get_event_loop()
    nsa = NSA()
    loop.set_debug(True)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(nsa.teardown())

if __name__ == "__main__":
    main()
