from argparse import Namespace
from ftw.crawler.configuration import Config
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import get_config
from ftw.crawler.configuration import Site
from ftw.crawler.exceptions import NoSuchField
from ftw.crawler.extractors import Extractor
from ftw.crawler.testing import CrawlerTestCase
from pkg_resources import resource_filename


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class TestConfig(CrawlerTestCase):

    def setUp(self):
        CrawlerTestCase.setUp(self)
        self.site = Site('http://example.org')
        self.tika = 'http://localhost:9998'
        self.solr = 'http://localhost:8983/solr'
        self.unique_field = 'UID'
        self.url_field = 'url'
        self.last_modified_field = 'modified'
        self.field = Field('foo', extractor=Extractor())

        self.config = Config([self.site], self.unique_field, self.url_field,
                             self.last_modified_field, [self.field],
                             self.tika, self.solr)

    def test_config_stores_sites(self):
        self.assertEquals([self.site], self.config.sites)

    def test_config_stores_tika(self):
        self.assertEquals(self.tika, self.config.tika)

    def test_config_stores_solr(self):
        self.assertEquals(self.solr, self.config.solr)

    def test_config_stores_unique_field(self):
        self.assertEquals(self.unique_field, self.config.unique_field)

    def test_config_stores_url_field(self):
        self.assertEquals(self.url_field, self.config.url_field)

    def test_config_stores_last_modified_field(self):
        self.assertEquals(
            self.last_modified_field, self.config.last_modified_field)

    def test_config_stores_fields(self):
        self.assertEquals([self.field], self.config.fields)

    def test_binds_fields_to_self(self):
        self.assertEquals(self.field.config, self.config)

    def test_binds_sites_to_self(self):
        self.assertEquals(self.site.config, self.config)

    def test_get_field_retrieves_field_by_name(self):
        field = self.config.get_field('foo')
        self.assertEquals(field, self.field)

    def test_get_field_raises_if_field_not_found(self):
        with self.assertRaises(NoSuchField):
            self.config.get_field('doesnt_exist')


class TestSite(CrawlerTestCase):

    def test_site_requires_url(self):
        with self.assertRaises(TypeError):
            Site()

    def test_site_stores_url(self):
        url = 'http://example.org'
        site = Site(url)
        self.assertEquals(url, site.url)

    def test_site_stores_attributes(self):
        url = 'http://example.org'
        attributes = {'name': 'My Site'}
        site = Site(url, attributes=attributes)
        self.assertEquals({'name': 'My Site'}, site.attributes)


class TestField(CrawlerTestCase):

    def setUp(self):
        CrawlerTestCase.setUp(self)
        self.name = 'Title'
        self.extractor = Extractor()
        self.type_ = str

    def test_field_stores_name(self):
        field = Field(self.name, self.extractor)
        self.assertEquals(self.name, field.name)

    def test_field_stores_extractor(self):
        field = Field(self.name, self.extractor)
        self.assertEquals(self.extractor, field.extractor)

    def test_field_stores_type(self):
        field = Field(self.name, self.extractor, self.type_)
        self.assertEquals(self.type_, field.type_)

    def test_field_stores_required(self):
        field = Field(self.name, self.extractor, self.type_, required=True)
        self.assertEquals(True, field.required)

    def test_field_binds_extractor_to_self(self):
        extractor = Extractor()
        field = Field(self.name, extractor, self.type_, required=True)
        self.assertEquals(field, extractor.field)


class TestGetConfig(CrawlerTestCase):

    def test_get_config_loads_config_module_and_returns_config_instance(self):
        options = Namespace(tika=None, solr=None)
        options.config = BASIC_CONFIG

        config = get_config(options)
        self.assertIsInstance(config, Config)

    def test_get_config_sets_tika_and_solr_from_command_line(self):
        options = Namespace(tika='http://tika', solr='http://solr')
        options.config = BASIC_CONFIG

        config = get_config(options)
        self.assertEquals('http://tika', config.tika)
        self.assertEquals('http://solr', config.solr)
