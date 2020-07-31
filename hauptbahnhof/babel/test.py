import asyncio
from hauptbahnhof import Hauptbahnhof

from hauptbahnhof.babel.babel import Babel


messages: asyncio.Queue = asyncio.Queue()


async def on_message(client, message, _):
    print("Got message: %s" % message)
    await messages.put(message)


async def test(loop):
    testbf = Hauptbahnhof("babel", loop=loop)
    testbf.subscribe("/haspa/licht/2/w", on_message)

    await asyncio.sleep(2)
    await testbf.publish("/haspa/licht", 1023)

    # Now everythin should be set up
    msg = await asyncio.wait_for(messages.get(), 10)  # wait max 10 secs
    for a in msg.values():
        for lamp_value in a:
            assert lamp_value == 1023

    await testbf.publish("/haspa/licht", 1023)
    msg = await asyncio.wait_for(messages.get(), 10)  # wait max 10 secs
    for espidx, a in msg.items():
        for lamp_idx, lamp_value in enumerate(a):
            if espidx == "esp1" and lamp_idx == 0:
                assert lamp_value == 42
            else:
                assert lamp_value == 1023

    try:
        await testbf.teardown()
    except asyncio.CancelledError:
        pass


def main():
    loop = asyncio.get_event_loop()
    lib = Babel(loop=loop)

    result = loop.run_until_complete(test(loop))
    loop.run_until_complete(lib.teardown())
    loop.set_debug(True)
    if result:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
