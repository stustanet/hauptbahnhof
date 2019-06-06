import asyncio
from hauptbahnhof import Hauptbahnhof

from mpd.mpd import MPD

async def test(loop):
    testbf = Hauptbahnhof("test", loop=loop)
    await asyncio.sleep(2)
    # Now everythin should be set up

    await testbf.publish("/haspa/music/control", {'play':True})

    # The music module is not sending any status back
    try:
        await testbf.teardown()
    except asyncio.CancelledError:
        pass

def main():
    loop = asyncio.get_event_loop()
    lib = MPD(loop=loop)

    result = loop.run_until_complete(test(loop))
    loop.run_until_complete(lib.teardown())

    if result:
        exit(0)
    else:
        exit(1)

if __name__=="__main__":
    main()
