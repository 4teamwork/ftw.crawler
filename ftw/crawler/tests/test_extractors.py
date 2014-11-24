from argparse import Namespace
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import get_config
from ftw.crawler.extractors import ExtractionEngine
from ftw.crawler.extractors import MetadataExtractor
from ftw.crawler.extractors import TitleExtractor
from ftw.crawler.tests.helpers import MockConverter
from mock import MagicMock
from pkg_resources import resource_filename
from unittest2 import TestCase


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class ExampleExtractor(MetadataExtractor):

    def extract_metadata(self, metadata):
        return metadata.get('example')


class TestMetadataExtractor(TestCase):

    def test_extract_metadata_raises_not_implemented(self):
        extractor = MetadataExtractor()
        with self.assertRaises(NotImplementedError):
            extractor.extract_metadata(metadata=None)


class TestExtractionEngine(TestCase):

    def setUp(self):
        args = Namespace()
        args.config = BASIC_CONFIG
        self.config = get_config(args)

    def test_applies_extractors_to_converter_metadata(self):
        mock_converter = MockConverter({'example': 'value', 'other': 'data'})
        field = Field('EXAMPLE', extractors=[ExampleExtractor()], type_=str)

        engine = ExtractionEngine(
            self.config, fileobj=None, content_type=None, filename=None,
            fields=[field], converter=mock_converter)

        self.assertEquals({'EXAMPLE': 'value'}, engine.extract_field_values())

    def test_gets_metadata_from_converter(self):
        mock_converter = MagicMock()
        mock_converter.extract_metadata = MagicMock(
            return_value={'foo': 'bar'})

        engine = ExtractionEngine(
            self.config, fileobj=None, content_type=None, filename=None,
            fields=[], converter=mock_converter)

        self.assertEquals({'foo': 'bar'}, engine.metadata)


class TestTitleExtractor(TestCase):

    def test_extracts_title(self):
        metadata = {'foo': None, 'title': 'value', 'bar': None}
        extractor = TitleExtractor()
        self.assertEquals('value', extractor.extract_metadata(metadata))
