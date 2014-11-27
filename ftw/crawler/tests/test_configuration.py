from argparse import Namespace
from ftw.crawler.configuration import Config
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import get_config
from ftw.crawler.configuration import Site
from ftw.crawler.extractors import Extractor
from pkg_resources import resource_filename
from unittest2 import TestCase


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class TestConfig(TestCase):

    def setUp(self):
        self.site = Site('http://example.org')
        self.tika = 'http://localhost:9998'
        self.solr = 'http://localhost:8983/solr'
        self.field = Field('foo', extractor=None)

        self.config = Config([self.site], self.tika, self.solr, [self.field])

    def test_config_stores_sites(self):
        self.assertEquals([self.site], self.config.sites)

    def test_config_stores_tika(self):
        self.assertEquals(self.tika, self.config.tika)

    def test_config_stores_solr(self):
        self.assertEquals(self.solr, self.config.solr)

    def test_config_stores_fields(self):
        self.assertEquals([self.field], self.config.fields)


class TestSite(TestCase):

    def test_site_requires_url(self):
        with self.assertRaises(TypeError):
            Site()

    def test_site_stores_url(self):
        url = 'http://example.org'
        site = Site(url)
        self.assertEquals(url, site.url)


class TestField(TestCase):

    def setUp(self):
        self.name = 'Title'
        self.extractor = Extractor()
        self.type_ = str

    def test_field_stores_name(self):
        field = Field(self.name, [self.extractor])
        self.assertEquals(self.name, field.name)

    def test_field_stores_extractor(self):
        field = Field(self.name, [self.extractor])
        self.assertEquals([self.extractor], field.extractor)

    def test_field_stores_type(self):
        field = Field(self.name, [self.extractor], self.type_)
        self.assertEquals(self.type_, field.type_)

    def test_field_stores_required(self):
        field = Field(self.name, [self.extractor], self.type_, required=True)
        self.assertEquals(True, field.required)


class TestGetConfig(TestCase):

    def test_get_config_loads_config_module_and_returns_config_instance(self):
        args = Namespace()
        args.config = BASIC_CONFIG

        config = get_config(args)
        self.assertIsInstance(config, Config)
