import asyncio
from hauptbahnhof import Hauptbahnhof

from hackerman.hackerman import Hackerman


messages = asyncio.Queue()
async def on_message(client, message, _):
    print("Got message: %s"%message)
    await messages.put(message)


async def test(loop):
    testbf = Hauptbahnhof(loop=loop)
    testbf.subscribe("/haspa/power", on_message)

    await asyncio.sleep(2)

    await testbf.publish("/haspa/status", {'haspa':'open'}) # without blacklist

    # Now everythin should be set up
    msg = await asyncio.wait_for(messages.get(), 10) # wait max 10 secs

    assert(msg['table'] == 1023)
    assert(msg['ledstrip'] == 400)

    try:
        await testbf.teardown()
    except asyncio.CancelledError:
        pass

def main():
    loop = asyncio.get_event_loop()
    lib = Hackerman(loop=loop)

    result = loop.run_until_complete(test(loop))
    loop.run_until_complete(lib.teardown())

    if result:
        exit(0)
    else:
        exit(1)

if __name__=="__main__":
    main()
