from ftw.crawler import parse_args
from mock import patch
from unittest2 import TestCase


class TestArgumentParsing(TestCase):

    @patch('sys.stderr')
    def test_positional_config_argument_is_required(self, stderr):
        with self.assertRaises(SystemExit):
            parse_args()
        self.assertIn('too few arguments', str(stderr.write.call_args))

    def test_positional_config_argument_is_parsed(self):
        argv = ['basic_config.py']

        args = parse_args(argv)
        self.assertEquals('basic_config.py', args.config)

    def test_optional_url_argument_is_parsed(self):
        argv = ['basic_config.py', 'http://example.org']

        args = parse_args(argv)
        self.assertEquals('http://example.org', args.url)
