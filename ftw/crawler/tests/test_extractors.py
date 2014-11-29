from argparse import Namespace
from datetime import datetime
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import get_config
from ftw.crawler.configuration import Site
from ftw.crawler.exceptions import ExtractionError
from ftw.crawler.exceptions import NoValueExtracted
from ftw.crawler.extractors import ConstantExtractor
from ftw.crawler.extractors import DescriptionExtractor
from ftw.crawler.extractors import ExtractionEngine
from ftw.crawler.extractors import Extractor
from ftw.crawler.extractors import HTTPHeaderExtractor
from ftw.crawler.extractors import IndexingTimeExtractor
from ftw.crawler.extractors import KeywordsExtractor
from ftw.crawler.extractors import LastModifiedExtractor
from ftw.crawler.extractors import MetadataExtractor
from ftw.crawler.extractors import PlainTextExtractor
from ftw.crawler.extractors import SiteAttributeExtractor
from ftw.crawler.extractors import SlugExtractor
from ftw.crawler.extractors import SnippetTextExtractor
from ftw.crawler.extractors import TextExtractor
from ftw.crawler.extractors import TitleExtractor
from ftw.crawler.extractors import UIDExtractor
from ftw.crawler.extractors import URLExtractor
from ftw.crawler.extractors import URLInfoExtractor
from ftw.crawler.testing import DatetimeTestCase
from ftw.crawler.tests.helpers import MockConverter
from ftw.crawler.utils import to_utc
from mock import MagicMock
from pkg_resources import resource_filename
from unittest2 import TestCase


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class ExampleMetadataExtractor(MetadataExtractor):

    def extract_value(self):
        value = self.metadata.get('example')
        if value is None:
            raise NoValueExtracted
        return value


class ExampleTextExtractor(TextExtractor):

    def extract_value(self):
        return self.text


class ExampleURLInfoExtractor(URLInfoExtractor):

    def extract_value(self):
        return self.url_info['loc']


class ExampleHTTPHeaderExtractor(HTTPHeaderExtractor):

    def __init__(self, header_name):
        self.header_name = header_name

    def extract_value(self):
        return self.headers[self.header_name]


class TestExtractionEngine(TestCase):

    def setUp(self):
        args = Namespace()
        args.config = BASIC_CONFIG
        self.config = get_config(args)

    def _create_engine(self, config=None, site=None, url_info=None,
                       fileobj=None, content_type=None, filename=None,
                       headers=None, fields=None, converter=None):
        if config is None:
            config = self.config

        if headers is None:
            self.headers = {}

        if fields is None:
            fields = []

        if converter is None:
            converter = MagicMock()

        engine = ExtractionEngine(
            config, site=site, url_info=url_info, fileobj=fileobj,
            content_type=content_type, filename=filename, headers=headers,
            fields=fields, converter=converter)
        return engine

    def test_applies_metadata_extractors_to_converter_metadata(self):
        converter = MockConverter({'example': 'value', 'other': 'data'})
        field = Field('EXAMPLE', extractor=ExampleMetadataExtractor())
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': 'value'}, engine.extract_field_values())

    def test_applies_text_extractors_to_converter_plain_text(self):
        converter = MockConverter(text='foo bar')
        field = Field(
            'EXAMPLE', extractor=ExampleTextExtractor())
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': 'foo bar'},
                          engine.extract_field_values())

    def test_applies_urlinfo_extractors_to_urlinfo(self):
        field = Field(
            'EXAMPLE', extractor=ExampleURLInfoExtractor())
        url_info = {'loc': 'http://example.org'}
        engine = self._create_engine(url_info=url_info, fields=[field])

        self.assertEquals({'EXAMPLE': 'http://example.org'},
                          engine.extract_field_values())

    def test_applies_site_config_extractors_to_site(self):
        field = Field(
            'EXAMPLE', extractor=SiteAttributeExtractor('name'))
        site = Site('http://example.org', attributes={'name': 'My Site'})
        engine = self._create_engine(site=site, fields=[field])

        self.assertEquals({'EXAMPLE': 'My Site'},
                          engine.extract_field_values())

    def test_applies_http_header_extractors_to_headers(self):
        field = Field(
            'EXAMPLE', extractor=ExampleHTTPHeaderExtractor('example-header'))
        headers = {'example-header': 'value'}
        engine = self._create_engine(headers=headers, fields=[field])

        self.assertEquals({'EXAMPLE': 'value'},
                          engine.extract_field_values())

    def test_gets_metadata_from_converter(self):
        converter = MagicMock()
        converter.extract_metadata = MagicMock(return_value={'foo': 'bar'})
        engine = self._create_engine(converter=converter)

        self.assertEquals({'foo': 'bar'}, engine.metadata)

    def test_gets_text_from_converter(self):
        converter = MagicMock()
        converter.extract_text = MagicMock(return_value='foo bar')
        engine = self._create_engine(converter=converter)

        self.assertEquals('foo bar', engine.text)

    def test_raises_type_error_for_unknown_extractor_type(self):
        field = Field('foo', extractor=object())
        engine = self._create_engine(fields=[field])

        with self.assertRaises(ExtractionError):
            engine.extract_field_values()

    def test_asserts_proper_type_for_extractors(self):
        field = Field('int_field',
                      extractor=ConstantExtractor('foo'),
                      type_=int)
        engine = self._create_engine(fields=[field])

        with self.assertRaises(ExtractionError):
            engine.extract_field_values()

    def test_asserts_proper_type_for_multivalued_extractors(self):
        field = Field('int_field',
                      extractor=ConstantExtractor([42]),
                      type_=int,
                      multivalued=True)
        engine = self._create_engine(fields=[field])

        self.assertEquals({'int_field': [42]}, engine.extract_field_values())

    def test_provides_default_for_required_fields(self):
        converter = MagicMock()
        converter.extract_metadata = MagicMock(return_value={})

        field = Field('required_field',
                      extractor=ExampleMetadataExtractor(),
                      type_=str,
                      required=True)
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals(
            {'required_field': ''}, engine.extract_field_values())

    def test_provides_default_for_required_datetime_fields(self):
        converter = MagicMock()
        converter.extract_metadata = MagicMock(return_value={})

        field = Field('required_datetime',
                      extractor=ExampleMetadataExtractor(),
                      type_=datetime,
                      required=True)
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals(
            {'required_datetime': datetime(1970, 1, 1, 0, 0)},
            engine.extract_field_values())

    def test_skips_field_if_no_value_extracted_and_field_not_required(self):
        converter = MagicMock()
        converter.extract_metadata = MagicMock(return_value={})

        field = Field('optional_field',
                      extractor=ExampleMetadataExtractor(),
                      type_=str)
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({}, engine.extract_field_values())


class TestExtractorBaseClass(TestCase):

    def test_extract_value_raises_not_implemented(self):
        extractor = Extractor()
        with self.assertRaises(NotImplementedError):
            extractor.extract_value()


class TestPlainTextExtractor(TestCase):

    def test_returns_given_text(self):
        extractor = PlainTextExtractor()
        extractor.text = 'foobar'
        self.assertEquals('foobar', extractor.extract_value())


class TestTitleExtractor(TestCase):

    def test_extracts_title(self):
        extractor = TitleExtractor()
        extractor.metadata = {'foo': None, 'title': 'value', 'bar': None}
        self.assertEquals('value', extractor.extract_value())

    def test_raises_if_no_value_found(self):
        extractor = TitleExtractor()
        extractor.metadata = {}
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value()


class TestDescriptionExtractor(TestCase):

    def test_extracts_description(self):
        extractor = DescriptionExtractor()
        extractor.metadata = {'foo': None, 'description': 'value', 'bar': None}
        self.assertEquals('value', extractor.extract_value())

    def test_raises_if_no_value_found(self):
        extractor = DescriptionExtractor()
        extractor.metadata = {}
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value()


class TestSnippetTextExtractor(TestCase):

    def test_returns_plain_text_if_title_not_present(self):
        extractor = SnippetTextExtractor()
        extractor.metadata = {}
        extractor.text = 'Lorem Ipsum'
        self.assertEquals('Lorem Ipsum', extractor.extract_value())

    def test_strips_title_from_beginning_of_plain_text(self):
        extractor = SnippetTextExtractor()
        extractor.metadata = {'title': 'My Title'}
        extractor.text = 'My Title\nLorem Ipsum'
        self.assertEquals('Lorem Ipsum', extractor.extract_value())


class TestLastModifiedExtractor(DatetimeTestCase):

    def test_lastmod_from_urlinfo(self):
        extractor = LastModifiedExtractor()
        extractor.url_info = {'lastmod': '2014-12-31T16:45:30+01:00'}
        self.assertEquals(to_utc(datetime(2014, 12, 31, 15, 45, 30)),
                          extractor.extract_value())

    def test_falls_back_to_http_last_modified(self):
        extractor = LastModifiedExtractor()
        extractor.url_info = {}
        extractor.headers = {'last-modified': 'Wed, 31 Dec 2014 15:45:30 GMT'}
        self.assertEquals(to_utc(datetime(2014, 12, 31, 15, 45, 30)),
                          extractor.extract_value())

    def test_falls_back_to_indexing_date(self):
        extractor = LastModifiedExtractor()
        extractor.url_info = {}
        extractor.headers = {}
        self.assertDatetimesAlmostEqual(
            datetime.utcnow(), extractor.extract_value())


class TestKeywordsExtractor(TestCase):

    def test_extracts_comma_separated_keywords(self):
        extractor = KeywordsExtractor()
        extractor.metadata = {'keywords': 'Foo, Bar,     Baz'}
        self.assertEquals(['Foo', 'Bar', 'Baz'], extractor.extract_value())

    def test_extracts_whitespace_separated_keywords(self):
        extractor = KeywordsExtractor()
        extractor.metadata = {'keywords': 'Foo Bar     Baz'}
        self.assertEquals(['Foo', 'Bar', 'Baz'], extractor.extract_value())

    def test_raises_if_no_value_found(self):
        extractor = KeywordsExtractor()
        extractor.metadata = {}
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value()


class TestUIDExtractor(TestCase):

    def test_builds_uid_based_on_url(self):
        extractor = UIDExtractor()
        extractor.url_info = {'loc': 'http://example.org'}
        self.assertEquals(
            'dab521de-65f9-250b-4cca-7383feef67dc', extractor.extract_value())

    def test_uid_stays_constant_for_same_url(self):
        extractor = UIDExtractor()
        extractor.url_info = {'loc': 'http://example.org'}
        uids = [extractor.extract_value() for i in range(10)]
        self.assertEquals(1, len(set(uids)))

    def test_uid_is_different_for_different_urls(self):
        extractor = UIDExtractor()

        extractor.url_info = {'loc': 'http://example.org'}
        uid1 = extractor.extract_value()

        extractor.url_info = {'loc': 'http://example.org/foo'}
        uid2 = extractor.extract_value()

        self.assertNotEqual(uid1, uid2)


class TestSlugExtractor(TestCase):

    def test_equals_basename_for_simple_urls(self):
        extractor = SlugExtractor()
        extractor.url_info = {'loc': 'http://example.org/foo/bar'}
        self.assertEquals('bar', extractor.extract_value())

    def test_deals_with_trailing_slash(self):
        extractor = SlugExtractor()
        extractor.url_info = {'loc': 'http://example.org/foo/bar/'}
        self.assertEquals('bar', extractor.extract_value())

    def test_defaults_to_index_html_for_empty_basename(self):
        extractor = SlugExtractor()
        extractor.url_info = {'loc': 'http://example.org/'}
        self.assertEquals('index-html', extractor.extract_value())

    def test_deals_with_url_encoding(self):
        extractor = SlugExtractor()
        extractor.url_info = {'loc': 'http://example.org/foo%%20bar'}
        self.assertEquals('foo-bar', extractor.extract_value())

    def test_deals_with_non_ascii_characters(self):
        extractor = SlugExtractor()
        extractor.url_info = {'loc': 'http://example.org/b\xc3\xa4rengraben'}
        self.assertEquals('barengraben', extractor.extract_value())


class TestURLExtractor(TestCase):

    def test_extracts_url_from_urlinfo(self):
        extractor = URLExtractor()
        extractor.url_info = {'loc': 'http://example.org'}
        self.assertEquals('http://example.org', extractor.extract_value())


class TestConstantExtractor(TestCase):

    def test_returns_constant_value(self):
        extractor = ConstantExtractor(42)
        self.assertEquals(42, extractor.extract_value())


class TestIndexingTimeExtractor(DatetimeTestCase):

    def test_returns_current_time(self):
        extractor = IndexingTimeExtractor()
        self.assertDatetimesAlmostEqual(datetime.utcnow(),
                                        extractor.extract_value())


class TestSiteAttributeExtractor(TestCase):

    def test_retrieves_attribute_from_site(self):
        site = Site('http://example.org', attributes={'name': 'My Site'})
        extractor = SiteAttributeExtractor('name')
        extractor.site = site

        self.assertEquals('My Site', extractor.extract_value())

    def test_raises_if_attribute_not_found(self):
        site = Site('http://example.org')
        extractor = SiteAttributeExtractor('name')
        extractor.site = site

        with self.assertRaises(NoValueExtracted):
            extractor.extract_value()
