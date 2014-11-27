from argparse import Namespace
from datetime import datetime
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import get_config
from ftw.crawler.exceptions import ExtractionError
from ftw.crawler.extractors import ConstantExtractor
from ftw.crawler.extractors import ExtractionEngine
from ftw.crawler.extractors import Extractor
from ftw.crawler.extractors import IndexingTimeExtractor
from ftw.crawler.extractors import MetadataExtractor
from ftw.crawler.extractors import PlainTextExtractor
from ftw.crawler.extractors import TextExtractor
from ftw.crawler.extractors import TitleExtractor
from ftw.crawler.extractors import UIDExtractor
from ftw.crawler.extractors import URLExtractor
from ftw.crawler.extractors import URLInfoExtractor
from ftw.crawler.testing import DatetimeTestCase
from ftw.crawler.tests.helpers import MockConverter
from mock import MagicMock
from pkg_resources import resource_filename
from unittest2 import TestCase


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class ExampleMetadataExtractor(MetadataExtractor):

    def extract_value(self):
        return self.metadata.get('example')


class ExampleTextExtractor(TextExtractor):

    def extract_value(self):
        return self.text


class ExampleURLInfoExtractor(URLInfoExtractor):

    def extract_value(self):
        return self.url_info['loc']


class TestExtractionEngine(TestCase):

    def setUp(self):
        args = Namespace()
        args.config = BASIC_CONFIG
        self.config = get_config(args)

    def _create_engine(self, config=None, url_info=None, fileobj=None,
                       content_type=None, filename=None, fields=None,
                       converter=None):
        if config is None:
            config = self.config

        if fields is None:
            fields = []

        if converter is None:
            converter = MagicMock()

        engine = ExtractionEngine(
            config, url_info=url_info, fileobj=fileobj,
            content_type=content_type, filename=filename, fields=fields,
            converter=converter)
        return engine

    def test_applies_metadata_extractors_to_converter_metadata(self):
        converter = MockConverter({'example': 'value', 'other': 'data'})
        field = Field('EXAMPLE', extractors=[ExampleMetadataExtractor()])
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': 'value'}, engine.extract_field_values())

    def test_applies_text_extractors_to_converter_plain_text(self):
        converter = MockConverter(text='foo bar')
        field = Field(
            'EXAMPLE', extractors=[ExampleTextExtractor()])
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': 'foo bar'},
                          engine.extract_field_values())

    def test_applies_urlinfo_extractors_to_urlinfo(self):
        field = Field(
            'EXAMPLE', extractors=[ExampleURLInfoExtractor()])
        url_info = {'loc': 'http://example.org'}
        engine = self._create_engine(url_info=url_info, fields=[field])

        self.assertEquals({'EXAMPLE': 'http://example.org'},
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
        field = Field('foo', extractors=[object()])
        engine = self._create_engine(fields=[field])

        with self.assertRaises(ExtractionError):
            engine.extract_field_values()

    def test_asserts_proper_type_for_extractors(self):
        field = Field('int_field',
                      extractors=[ConstantExtractor('foo')],
                      type_=int)
        engine = self._create_engine(fields=[field])

        with self.assertRaises(ExtractionError):
            engine.extract_field_values()

    def test_asserts_proper_type_for_multivalued_extractors(self):
        field = Field('int_field',
                      extractors=[ConstantExtractor([42])],
                      type_=int,
                      multivalued=True)
        engine = self._create_engine(fields=[field])

        self.assertEquals({'int_field': [42]}, engine.extract_field_values())


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
