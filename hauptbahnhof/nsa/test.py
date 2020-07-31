import asyncio
import queue
import time
from hauptbahnhof import Hauptbahnhof

from hauptbahnhof.nsa.nsa import NSA


messages: queue.Queue = queue.Queue()


def on_message(client, message, _):
    print("Got message: %s" % message)
    messages.put(message)


def test():
    testbf = Hauptbahnhof("test")
    testbf.subscribe("/haspa/nsa/result", on_message)

    time.sleep(2)

    testbf.publish("/haspa/nsa/scan", {})  # without blacklist

    # Now everythin should be set up
    msg = messages.get()  # wait max 10 secs

    if msg["count"] > 0:
        testbf.log.info("test successfull")
        return True
    else:
        raise ValueError("test failed")


def main():
    lib = NSA()
    asyncio.get_event_loop().run_in_executor(lib.run)
    result = test()

    if result:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
