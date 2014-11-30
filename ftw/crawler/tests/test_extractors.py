from argparse import Namespace
from copy import deepcopy
from datetime import datetime
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import get_config
from ftw.crawler.configuration import Site
from ftw.crawler.exceptions import ExtractionError
from ftw.crawler.exceptions import NoValueExtracted
from ftw.crawler.extractors import ConstantExtractor
from ftw.crawler.extractors import CreatorExtractor
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
from ftw.crawler.resource import ResourceInfo
from ftw.crawler.testing import DatetimeTestCase
from ftw.crawler.tests.helpers import MockConverter
from ftw.crawler.utils import to_utc
from mock import MagicMock
from pkg_resources import resource_filename
from unittest2 import TestCase


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class ExampleMetadataExtractor(MetadataExtractor):

    def extract_value(self, resource_info):
        value = resource_info.metadata.get('example')
        if value is None:
            raise NoValueExtracted
        return value


class ExampleTextExtractor(TextExtractor):

    def extract_value(self, resource_info):
        return resource_info.text


class ExampleURLInfoExtractor(URLInfoExtractor):

    def extract_value(self, resource_info):
        return resource_info.url_info['loc']


class ExampleHTTPHeaderExtractor(HTTPHeaderExtractor):

    def __init__(self, header_name):
        self.header_name = header_name

    def extract_value(self, resource_info):
        return resource_info.headers[self.header_name]


class TestExtractionEngine(TestCase):

    def setUp(self):
        args = Namespace()
        args.config = BASIC_CONFIG
        self.config = deepcopy(get_config(args))

    def _create_engine(self, config=None, fields=None, resource_info=None,
                       converter=None):
        if config is None:
            config = self.config

        if fields is not None:
            self.config.fields = fields

        if resource_info is None:
            resource_info = ResourceInfo()

        if converter is None:
            converter = MagicMock()

        engine = ExtractionEngine(
            config, resource_info=resource_info, converter=converter)
        return engine

    def test_applies_metadata_extractors_to_converter_metadata(self):
        converter = MockConverter({'example': 'value', 'other': 'data'})
        field = Field('EXAMPLE', extractor=ExampleMetadataExtractor())
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': 'value'}, engine.extract_field_values())

    def test_applies_text_extractors_to_converter_plain_text(self):
        converter = MockConverter(text='foo bar')
        field = Field('EXAMPLE', extractor=ExampleTextExtractor())
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': 'foo bar'},
                          engine.extract_field_values())

    def test_applies_urlinfo_extractors_to_urlinfo(self):
        field = Field('EXAMPLE', extractor=ExampleURLInfoExtractor())
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org'})
        engine = self._create_engine(
            resource_info=resource_info, fields=[field])

        self.assertEquals({'EXAMPLE': 'http://example.org'},
                          engine.extract_field_values())

    def test_applies_site_config_extractors_to_site(self):
        field = Field('EXAMPLE', extractor=SiteAttributeExtractor('name'))
        site = Site('http://example.org', attributes={'name': 'My Site'})
        resource_info = ResourceInfo(site=site)
        engine = self._create_engine(
            fields=[field], resource_info=resource_info)

        self.assertEquals({'EXAMPLE': 'My Site'},
                          engine.extract_field_values())

    def test_applies_http_header_extractors_to_headers(self):
        field = Field(
            'EXAMPLE', extractor=ExampleHTTPHeaderExtractor('example-header'))
        resource_info = ResourceInfo(headers={'example-header': 'value'})
        engine = self._create_engine(
            fields=[field], resource_info=resource_info)

        self.assertEquals({'EXAMPLE': 'value'},
                          engine.extract_field_values())

    def test_set_metadata_from_converter_on_resource_info(self):
        converter = MagicMock()
        converter.extract_metadata = MagicMock(return_value={'foo': 'bar'})
        resource_info = ResourceInfo()

        self._create_engine(resource_info=resource_info, converter=converter)
        self.assertEquals({'foo': 'bar'}, resource_info.metadata)

    def test_sets_text_from_converter_on_resource_info(self):
        converter = MagicMock()
        converter.extract_text = MagicMock(return_value='foo bar')
        resource_info = ResourceInfo()

        self._create_engine(resource_info=resource_info, converter=converter)
        self.assertEquals('foo bar', resource_info.text)

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
        resource_info = ResourceInfo()
        with self.assertRaises(NotImplementedError):
            extractor.extract_value(resource_info)


class TestPlainTextExtractor(TestCase):

    def test_returns_given_text(self):
        extractor = PlainTextExtractor()
        resource_info = ResourceInfo(text='foobar')
        self.assertEquals('foobar', extractor.extract_value(resource_info))


class TestTitleExtractor(TestCase):

    def test_extracts_title(self):
        extractor = TitleExtractor()
        resource_info = ResourceInfo(metadata={'title': 'value'})
        self.assertEquals('value', extractor.extract_value(resource_info))

    def test_raises_if_no_value_found(self):
        extractor = TitleExtractor()
        resource_info = ResourceInfo(metadata={})
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestDescriptionExtractor(TestCase):

    def test_extracts_description(self):
        extractor = DescriptionExtractor()
        resource_info = ResourceInfo(metadata={'description': 'value'})
        self.assertEquals('value', extractor.extract_value(resource_info))

    def test_raises_if_no_value_found(self):
        extractor = DescriptionExtractor()
        resource_info = ResourceInfo(metadata={})
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestCreatorExtractor(TestCase):

    def test_extracts_creator(self):
        extractor = CreatorExtractor()
        resource_info = ResourceInfo(metadata={'creator': 'John Doe'})
        self.assertEquals('John Doe', extractor.extract_value(resource_info))

    def test_raises_if_no_value_found(self):
        extractor = CreatorExtractor()
        resource_info = ResourceInfo(metadata={})
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestSnippetTextExtractor(TestCase):

    def test_returns_plain_text_if_title_not_present(self):
        extractor = SnippetTextExtractor()
        resource_info = ResourceInfo(metadata={}, text='Lorem Ipsum')
        self.assertEquals(
            'Lorem Ipsum', extractor.extract_value(resource_info))

    def test_strips_title_from_beginning_of_plain_text(self):
        extractor = SnippetTextExtractor()
        resource_info = ResourceInfo(
            metadata={'title': 'My Title'},
            text='My Title\nLorem Ipsum')
        self.assertEquals(
            'Lorem Ipsum', extractor.extract_value(resource_info))


class TestLastModifiedExtractor(DatetimeTestCase):

    def test_lastmod_from_urlinfo(self):
        extractor = LastModifiedExtractor()
        resource_info = ResourceInfo(
            url_info={'lastmod': '2014-12-31T16:45:30+01:00'})

        self.assertEquals(to_utc(datetime(2014, 12, 31, 15, 45, 30)),
                          extractor.extract_value(resource_info))

    def test_falls_back_to_http_last_modified(self):
        extractor = LastModifiedExtractor()
        resource_info = ResourceInfo(
            url_info={},
            headers={'last-modified': 'Wed, 31 Dec 2014 15:45:30 GMT'})
        self.assertEquals(to_utc(datetime(2014, 12, 31, 15, 45, 30)),
                          extractor.extract_value(resource_info))

    def test_falls_back_to_indexing_date(self):
        extractor = LastModifiedExtractor()
        resource_info = ResourceInfo(url_info={}, headers={})
        self.assertDatetimesAlmostEqual(
            datetime.utcnow(), extractor.extract_value(resource_info))


class TestKeywordsExtractor(TestCase):

    def test_extracts_comma_separated_keywords(self):
        extractor = KeywordsExtractor()
        resource_info = ResourceInfo(
            metadata={'keywords': 'Foo, Bar,     Baz'})
        self.assertEquals(
            ['Foo', 'Bar', 'Baz'], extractor.extract_value(resource_info))

    def test_extracts_whitespace_separated_keywords(self):
        extractor = KeywordsExtractor()
        resource_info = ResourceInfo(metadata={'keywords': 'Foo Bar     Baz'})
        self.assertEquals(
            ['Foo', 'Bar', 'Baz'], extractor.extract_value(resource_info))

    def test_raises_if_no_value_found(self):
        extractor = KeywordsExtractor()
        resource_info = ResourceInfo(metadata={})
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestUIDExtractor(TestCase):

    def test_builds_uid_based_on_url(self):
        extractor = UIDExtractor()
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org'})
        self.assertEquals('dab521de-65f9-250b-4cca-7383feef67dc',
                          extractor.extract_value(resource_info))

    def test_uid_stays_constant_for_same_url(self):
        extractor = UIDExtractor()
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org'})
        uids = [extractor.extract_value(resource_info) for i in range(10)]
        self.assertEquals(1, len(set(uids)))

    def test_uid_is_different_for_different_urls(self):
        extractor = UIDExtractor()

        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org'})
        uid1 = extractor.extract_value(resource_info)

        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/foo'})
        uid2 = extractor.extract_value(resource_info)

        self.assertNotEqual(uid1, uid2)


class TestSlugExtractor(TestCase):

    def test_equals_basename_for_simple_urls(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/foo/bar'})
        self.assertEquals('bar', extractor.extract_value(resource_info))

    def test_deals_with_trailing_slash(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/foo/bar/'})
        self.assertEquals('bar', extractor.extract_value(resource_info))

    def test_defaults_to_index_html_for_empty_basename(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/'})
        self.assertEquals('index-html', extractor.extract_value(resource_info))

    def test_deals_with_url_encoding(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/foo%%20bar'})
        self.assertEquals('foo-bar', extractor.extract_value(resource_info))

    def test_deals_with_non_ascii_characters_utf8(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/b\xc3\xa4rengraben'})
        self.assertEquals(
            'barengraben', extractor.extract_value(resource_info))

    def test_deals_with_non_ascii_characters_unicode(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': u'http://example.org/b\xe4rengraben'})
        self.assertEquals(
            'barengraben', extractor.extract_value(resource_info))


class TestURLExtractor(TestCase):

    def test_extracts_url_from_urlinfo(self):
        extractor = URLExtractor()
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org'})
        self.assertEquals('http://example.org',
                          extractor.extract_value(resource_info))


class TestConstantExtractor(TestCase):

    def test_returns_constant_value(self):
        extractor = ConstantExtractor(42)
        resource_info = ResourceInfo()
        self.assertEquals(42, extractor.extract_value(resource_info))


class TestIndexingTimeExtractor(DatetimeTestCase):

    def test_returns_current_time(self):
        extractor = IndexingTimeExtractor()
        resource_info = ResourceInfo()
        self.assertDatetimesAlmostEqual(datetime.utcnow(),
                                        extractor.extract_value(resource_info))


class TestSiteAttributeExtractor(TestCase):

    def test_retrieves_attribute_from_site(self):
        site = Site('http://example.org', attributes={'name': 'My Site'})
        extractor = SiteAttributeExtractor('name')
        resource_info = ResourceInfo(site=site)

        self.assertEquals('My Site', extractor.extract_value(resource_info))

    def test_raises_if_attribute_not_found(self):
        site = Site('http://example.org')
        extractor = SiteAttributeExtractor('name')
        resource_info = ResourceInfo(site=site)

        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)
