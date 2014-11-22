from argparse import Namespace
from ftw.crawler.configuration import Config
from ftw.crawler.configuration import get_config
from ftw.crawler.configuration import Site
from pkg_resources import resource_filename
from unittest2 import TestCase


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class TestConfig(TestCase):

    def test_config_requires_sites(self):
        with self.assertRaises(TypeError):
            Config()

    def test_config_stores_sites(self):
        site = Site('http://example.org')
        config = Config([site])
        self.assertEquals([site], config.sites)


class TestSite(TestCase):

    def test_site_requires_url(self):
        with self.assertRaises(TypeError):
            Site()

    def test_site_stores_url(self):
        url = 'http://example.org'
        site = Site(url)
        self.assertEquals(url, site.url)


class TestGetConfig(TestCase):

    def test_get_config_loads_config_module_and_returns_config_instance(self):
        args = Namespace()
        args.config = BASIC_CONFIG

        config = get_config(args)
        self.assertIsInstance(config, Config)
