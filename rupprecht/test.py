import asyncio
from hauptbahnhof import Hauptbahnhof

from rupprecht.rupprecht import Rupprecht

async def test(loop):
    testbf = Hauptbahnhof(loop=loop)

    await asyncio.sleep(2)

    await testbf.publish("/haspa/status", {'haspa':'open'}) # without blacklist

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
