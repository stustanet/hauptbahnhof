import asyncio
from hauptbahnhof import Hauptbahnhof

from nsa.nsa import NSA


messages: asyncio.Queue = asyncio.Queue()


async def on_message(client, message, _):
    print("Got message: %s" % message)
    await messages.put(message)


async def test(loop):
    testbf = Hauptbahnhof("test", loop=loop)
    testbf.subscribe("/haspa/nsa/result", on_message)

    await asyncio.sleep(2)

    await testbf.publish("/haspa/nsa/scan", {})  # without blacklist

    # Now everythin should be set up
    msg = await asyncio.wait_for(messages.get(), 10)  # wait max 10 secs

    if msg["count"] > 0:
        testbf.log.info("test successfull")
        return True
    else:
        raise ValueError("test failed")

    try:
        await testbf.teardown()
    except asyncio.CancelledError:
        pass


def main():
    loop = asyncio.get_event_loop()
    lib = NSA(loop=loop)

    result = loop.run_until_complete(test(loop))
    loop.run_until_complete(lib.teardown())

    if result:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
