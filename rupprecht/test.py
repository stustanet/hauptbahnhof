import asyncio
from hauptbahnhof import Hauptbahnhof

from rupprecht.rupprecht import Rupprecht


messages = asyncio.Queue()
async def on_message(client, message, _):
    print("Got message: %s"%message)
    await messages.put(message)


async def test(loop):
    testbf = Hauptbahnhof(loop=loop)
    await asyncio.sleep(2)
    # Now everythin should be set up

    await testbf.publish("/haspa/led", {'rupprecht-table':1023})

    # This module is not sending any status back
    try:
        await testbf.teardown()
    except asyncio.CancelledError:
        pass

def main():
    loop = asyncio.get_event_loop()
    lib = Rupprecht(loop=loop)

    result = loop.run_until_complete(test(loop))
    loop.run_until_complete(lib.teardown())

    if result:
        exit(0)
    else:
        exit(1)

if __name__=="__main__":
    main()
