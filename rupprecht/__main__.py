import asyncio

from rupprecht.rupprecht import Rupprecht

def main():
    """
    Actually start the shit
    """
    loop = asyncio.get_event_loop()
    rup = Rupprecht()
    loop.set_debug(True)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(rup.teardown())

if __name__ == "__main__":
    main()
