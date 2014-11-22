from ftw.crawler import parse_args
from unittest2 import TestCase


class TestArgumentParsing(TestCase):

    def test_positional_config_argument_is_required(self):
        with self.assertRaises(SystemExit):
            parse_args()

    def test_positional_config_argument_is_parsed(self):
        argv = ['basic_config.py']

        args = parse_args(argv)
        self.assertEquals('basic_config.py', args.config)
