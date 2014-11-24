import argparse
import logging
import sys


logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-10s %(module)-16s %(message)s')


def parse_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to the config file')
    args = parser.parse_args(argv)
    return args
