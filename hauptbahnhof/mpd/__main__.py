from hauptbahnhof.mpd import MPD


def main():
    """
    Actually start the shit
    """
    mpd = MPD()
    mpd.run()


if __name__ == "__main__":
    main()
