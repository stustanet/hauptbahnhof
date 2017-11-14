from .hauptbahnhof import *

import argparse
import configparser

DEFAULT_CONFIG = "/home/hauptbahnhof/config.ini"

def main():

    # parse command line arguments
    cmd = argparse.ArgumentParser()
    cmd.add_argument("-c","--config", default=DEFAULT_CONFIG,
                     help = "Path to the configuration file")
    args = cmd.parse_args()

    # parse config file
    config = configparser.ConfigParser()
    config.sections()
    config.read(args.config)

    try:
        listen_addr = config['Server']['LISTEN_ADDR']
        listen_port = config['Server']['LISTEN_PORT']
        server_cert = config['Server']['SERVER_CERT']
        server_key = config['Server']['SERVER_KEY']
        allowed_client_certs = config['Server']['ALLOWED_CLIENT_CERTS']

        space_netdev = config['Hackerspace']['SPACE_NETDEV']
        stat_devices = config['Hackerspace']['STAT_DEVICES'].split()
        space_network = config['Hackerspace']['SPACE_NETWORK']

    except KeyError as e:
        print("Missing key/value in config file:", e)
        return -1

    # init a new Hackerspace object
    space = Hackerspace(space_netdev, stat_devices, space_network)

    # start the Hauptbahnhof server
    h = Hauptbahnhof(listen_addr,
                     listen_port,
                     server_cert,
                     server_key,
                     allowed_client_certs,
                     space)

if __name__ == "__main__":
    main()
