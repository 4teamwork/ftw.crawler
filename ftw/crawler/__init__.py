from ftw.crawler.log import setup_logging
import argparse
import sys


setup_logging()


def parse_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Path to the config file')
    parser.add_argument('url', help='If given, only index the supplied URL',
                        nargs='?', default=None)
    parser.add_argument('--tika', help='Base URL to Tika', metavar='TIKA_URL')
    parser.add_argument('--solr', help='Base URL to Solr', metavar='SOLR_URL')
    parser.add_argument('-f', '--force', help="Force crawling even if"
                        "document hasn't been modified", action='store_true')
    args = parser.parse_args(argv)

    return args
