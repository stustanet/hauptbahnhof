import time

from hauptbahnhof import Hauptbahnhof


def main():
    testbf = Hauptbahnhof(
        "test",
    )

    time.sleep(2)

    testbf.publish("/haspa/status", {"haspa": "open"})  # without blacklist


if __name__ == "__main__":
    main()
