from haspa_web.haspa import HaspaWeb

def main():
    """
    Actually start the shit
    """
    haspaweb = HaspaWeb()
    haspaweb.hbf.start(spinoff=False)

if __name__ == "__main__":
    main()
