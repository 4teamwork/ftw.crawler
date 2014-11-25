from argparse import Namespace
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import get_config
from ftw.crawler.extractors import ExtractionEngine
from ftw.crawler.extractors import MetadataExtractor
from ftw.crawler.extractors import PlainTextExtractor
from ftw.crawler.extractors import TextExtractor
from ftw.crawler.extractors import TitleExtractor
from ftw.crawler.tests.helpers import MockConverter
from mock import MagicMock
from pkg_resources import resource_filename
from unittest2 import TestCase


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class ExampleExtractor(MetadataExtractor):

    def extract_metadata(self, metadata):
        return metadata.get('example')


class ExampleTextExtractor(TextExtractor):

    def extract_text(self, text):
        return text


class TestExtractionEngine(TestCase):

    def setUp(self):
        args = Namespace()
        args.config = BASIC_CONFIG
        self.config = get_config(args)

    def test_applies_extractors_to_converter_metadata(self):
        converter = MockConverter({'example': 'value', 'other': 'data'})
        field = Field('EXAMPLE', extractors=[ExampleExtractor()])

        engine = ExtractionEngine(
            self.config, fileobj=None, content_type=None, filename=None,
            fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': 'value'}, engine.extract_field_values())

    def test_applies_extractors_to_converter_plain_text(self):
        converter = MockConverter(text='foo bar')
        field = Field(
            'EXAMPLE', extractors=[ExampleTextExtractor()])

        engine = ExtractionEngine(
            self.config, fileobj=None, content_type=None, filename=None,
            fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': 'foo bar'},
                          engine.extract_field_values())

    def test_gets_metadata_from_converter(self):
        converter = MagicMock()
        converter.extract_metadata = MagicMock(return_value={'foo': 'bar'})

        engine = ExtractionEngine(
            self.config, fileobj=None, content_type=None, filename=None,
            fields=[], converter=converter)

        self.assertEquals({'foo': 'bar'}, engine.metadata)

    def test_gets_text_from_converter(self):
        converter = MagicMock()
        converter.extract_text = MagicMock(return_value='foo bar')

        engine = ExtractionEngine(
            self.config, fileobj=None, content_type=None, filename=None,
            fields=[], converter=converter)

        self.assertEquals('foo bar', engine.text)

    def test_raises_type_error_for_unknown_extractor_type(self):
        extractor = object()
        field = Field('foo', extractors=[extractor])
        engine = ExtractionEngine(
            self.config, fileobj=None, content_type=None, filename=None,
            fields=[field], converter=MagicMock())

        with self.assertRaises(TypeError):
            engine.extract_field_values()


class TestMetadataExtractor(TestCase):

    def test_extract_metadata_raises_not_implemented(self):
        extractor = MetadataExtractor()
        with self.assertRaises(NotImplementedError):
            extractor.extract_metadata(metadata=None)


class TestTextExtractor(TestCase):

    def test_extract_text_raises_not_implemented(self):
        extractor = TextExtractor()
        with self.assertRaises(NotImplementedError):
            extractor.extract_text(text='')


class TestTitleExtractor(TestCase):

    def test_extracts_title(self):
        metadata = {'foo': None, 'title': 'value', 'bar': None}
        extractor = TitleExtractor()
        self.assertEquals('value', extractor.extract_metadata(metadata))


class TestPlainTextExtractor(TestCase):

    def test_returns_given_text(self):
        text = 'foobar'
        extractor = PlainTextExtractor()
        self.assertEquals('foobar', extractor.extract_text(text))
