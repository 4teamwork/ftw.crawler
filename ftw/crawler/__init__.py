import argparse
import logging
import sys


logging.basicConfig(level=logging.DEBUG)


def parse_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to the config file')
    args = parser.parse_args(argv)
    return args
