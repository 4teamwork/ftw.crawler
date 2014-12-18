from argparse import Namespace
from copy import deepcopy
from datetime import datetime
from ftw.crawler.configuration import Config
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import get_config
from ftw.crawler.configuration import Site
from ftw.crawler.exceptions import ExtractionError
from ftw.crawler.exceptions import NoSuchField
from ftw.crawler.exceptions import NoValueExtracted
from ftw.crawler.extractors import ConstantExtractor
from ftw.crawler.extractors import CreatorExtractor
from ftw.crawler.extractors import DescriptionExtractor
from ftw.crawler.extractors import ExtractionEngine
from ftw.crawler.extractors import Extractor
from ftw.crawler.extractors import FieldMappingExtractor
from ftw.crawler.extractors import FilenameExtractor
from ftw.crawler.extractors import HeaderMappingExtractor
from ftw.crawler.extractors import HTTPHeaderExtractor
from ftw.crawler.extractors import IndexingTimeExtractor
from ftw.crawler.extractors import KeywordsExtractor
from ftw.crawler.extractors import LastModifiedExtractor
from ftw.crawler.extractors import MetadataExtractor
from ftw.crawler.extractors import PlainTextExtractor
from ftw.crawler.extractors import SiteAttributeExtractor
from ftw.crawler.extractors import SlugExtractor
from ftw.crawler.extractors import SnippetTextExtractor
from ftw.crawler.extractors import TargetURLExtractor
from ftw.crawler.extractors import TextExtractor
from ftw.crawler.extractors import TitleExtractor
from ftw.crawler.extractors import UIDExtractor
from ftw.crawler.extractors import URLExtractor
from ftw.crawler.extractors import URLInfoExtractor
from ftw.crawler.extractors import XPathExtractor
from ftw.crawler.resource import ResourceInfo
from ftw.crawler.testing import CrawlerTestCase
from ftw.crawler.testing import DatetimeTestCase
from ftw.crawler.tests.helpers import MockConverter
from ftw.crawler.utils import safe_unicode
from ftw.crawler.utils import to_utc
from mock import MagicMock
from pkg_resources import resource_filename


BASIC_CONFIG = resource_filename('ftw.crawler.tests.assets', 'basic_config.py')


class ExampleMetadataExtractor(MetadataExtractor):

    def extract_value(self, resource_info):
        value = resource_info.metadata.get('example')
        if value is None:
            raise NoValueExtracted
        return safe_unicode(value)


class ExampleTextExtractor(TextExtractor):

    def extract_value(self, resource_info):
        return resource_info.text


class ExampleURLInfoExtractor(URLInfoExtractor):

    def extract_value(self, resource_info):
        return safe_unicode(resource_info.url_info['loc'])


class ExampleHTTPHeaderExtractor(HTTPHeaderExtractor):

    def __init__(self, header_name):
        self.header_name = header_name

    def extract_value(self, resource_info):
        header_value = resource_info.headers[self.header_name]
        # In the rare case of non-ASCII characters in HTTP header field values,
        # we can assume them to be in ISO-8859-1 (see RFC 7230, section 3.2.4)
        return header_value.decode('latin1')


class TestExtractionEngine(CrawlerTestCase):

    def setUp(self):
        CrawlerTestCase.setUp(self)
        args = Namespace(tika=None, solr=None)
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
        converter = MockConverter({'example': u'value', 'other': u'data'})
        field = Field('EXAMPLE', extractor=ExampleMetadataExtractor())
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': u'value'}, engine.extract_field_values())

    def test_applies_text_extractors_to_converter_plain_text(self):
        converter = MockConverter(text=u'foo bar')
        field = Field('EXAMPLE', extractor=ExampleTextExtractor())
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({'EXAMPLE': u'foo bar'},
                          engine.extract_field_values())

    def test_applies_urlinfo_extractors_to_urlinfo(self):
        field = Field('EXAMPLE', extractor=ExampleURLInfoExtractor())
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org'})
        engine = self._create_engine(
            resource_info=resource_info, fields=[field])

        self.assertEquals({'EXAMPLE': u'http://example.org'},
                          engine.extract_field_values())

    def test_applies_site_config_extractors_to_site(self):
        field = Field('EXAMPLE', extractor=SiteAttributeExtractor('name'))
        site = Site('http://example.org', attributes={'name': 'My Site'})
        resource_info = ResourceInfo(site=site)
        engine = self._create_engine(
            fields=[field], resource_info=resource_info)

        self.assertEquals({'EXAMPLE': u'My Site'},
                          engine.extract_field_values())

    def test_applies_http_header_extractors_to_headers(self):
        field = Field(
            'EXAMPLE', extractor=ExampleHTTPHeaderExtractor('example-header'))
        resource_info = ResourceInfo(headers={'example-header': 'value'})
        engine = self._create_engine(
            fields=[field], resource_info=resource_info)

        self.assertEquals({'EXAMPLE': u'value'},
                          engine.extract_field_values())

    def test_set_metadata_from_converter_on_resource_info(self):
        converter = MagicMock()
        converter.extract_metadata = MagicMock(return_value={'foo': 'bar'})
        resource_info = ResourceInfo()

        self._create_engine(resource_info=resource_info, converter=converter)
        self.assertEquals({'foo': 'bar'}, resource_info.metadata)

    def test_sets_text_from_converter_on_resource_info(self):
        converter = MagicMock()
        converter.extract_text = MagicMock(return_value=u'foo bar')
        resource_info = ResourceInfo()

        self._create_engine(resource_info=resource_info, converter=converter)
        self.assertEquals(u'foo bar', resource_info.text)

    def test_raises_type_error_for_unknown_extractor_type(self):
        field = Field('foo', extractor=Extractor())
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
                      type_=unicode,
                      required=True)
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals(
            {'required_field': u''}, engine.extract_field_values())

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
                      type_=unicode)
        engine = self._create_engine(fields=[field], converter=converter)

        self.assertEquals({}, engine.extract_field_values())


class TestExtractorBaseClass(CrawlerTestCase):

    def test_extract_value_raises_not_implemented(self):
        extractor = Extractor()
        resource_info = ResourceInfo()
        with self.assertRaises(NotImplementedError):
            extractor.extract_value(resource_info)


class TestPlainTextExtractor(CrawlerTestCase):

    def test_returns_given_text(self):
        extractor = PlainTextExtractor()
        resource_info = ResourceInfo(text=u'foobar')
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'foobar', extracted_value)
        self.assertIsInstance(extracted_value, unicode)


class TestTitleExtractor(CrawlerTestCase):

    def test_extracts_title_from_x_document_title_http_header(self):
        extractor = TitleExtractor()
        resource_info = ResourceInfo(
            metadata={'title': u'dont-use-this'},
            headers={'X-Document-Title': 'QsOkcmVuZ3JhYmVuCg=='})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'B\xe4rengraben', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_extracts_title_from_metadata(self):
        extractor = TitleExtractor()
        resource_info = ResourceInfo(metadata={'title': u'value'},
                                     headers={})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'value', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_falls_back_to_filename(self):
        extractor = TitleExtractor()
        resource_info = ResourceInfo(
            metadata={},
            headers={'content-disposition': 'attachment; '
                     'filename="document.pdf"'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'document.pdf', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_falls_back_to_url_slug(self):
        extractor = TitleExtractor()
        resource_info = ResourceInfo(
            metadata={},
            headers={},
            url_info={'loc': 'http://example.org/my____title'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'my-title', extracted_value)
        self.assertIsInstance(extracted_value, unicode)


class TestXpathExtractor(CrawlerTestCase):

    def setUp(self):
        CrawlerTestCase.setUp(self)
        self.extractor = XPathExtractor("//div[@id='content']/h1")

    def _create_resource(self, asset_name):
        doc_fn = resource_filename('ftw.crawler.tests.assets', asset_name)
        resource_info = ResourceInfo(
            metadata={},
            url_info={'loc': 'http//example.org'},
            headers={},
            filename=doc_fn,
            content_type='text/html')
        return resource_info

    def test_extracts_text_from_node_by_xpath_from_html5_doc(self):
        resource_info = self._create_resource('html5_doc.html')
        extracted_value = self.extractor.extract_value(resource_info)

        self.assertEquals(u'Der B\xe4rengraben', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_extracts_text_from_node_by_xpath_from_xhtml_doc(self):
        resource_info = self._create_resource('xhtml_doc.html')
        extracted_value = self.extractor.extract_value(resource_info)

        self.assertEquals(u'Der B\xe4rengraben', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_selects_first_if_multiple_nodes_match(self):
        resource_info = self._create_resource('xhtml_doc.html')
        extractor = XPathExtractor("//p")
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'Foo', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_raises_if_no_nodes_matched(self):
        resource_info = self._create_resource('xhtml_doc.html')
        extractor = XPathExtractor("//doesntexist")
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestDescriptionExtractor(CrawlerTestCase):

    def test_extracts_description(self):
        extractor = DescriptionExtractor()
        resource_info = ResourceInfo(metadata={'description': 'value'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'value', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_raises_if_no_value_found(self):
        extractor = DescriptionExtractor()
        resource_info = ResourceInfo(metadata={})
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestCreatorExtractor(CrawlerTestCase):

    def test_extracts_creator(self):
        extractor = CreatorExtractor()
        resource_info = ResourceInfo(metadata={'creator': 'John Doe'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'John Doe', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_raises_if_no_value_found(self):
        extractor = CreatorExtractor()
        resource_info = ResourceInfo(metadata={})
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestSnippetTextExtractor(CrawlerTestCase):

    def test_returns_plain_text_if_title_not_present(self):
        extractor = SnippetTextExtractor()
        resource_info = ResourceInfo(
            metadata={'title': 'Foo'},
            text='Lorem Ipsum',
            headers={})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'Lorem Ipsum', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_strips_title_from_beginning_of_plain_text(self):
        extractor = SnippetTextExtractor()
        resource_info = ResourceInfo(
            metadata={'title': 'My Title'},
            text='My Title\nLorem Ipsum',
            headers={})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'Lorem Ipsum', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_handles_non_ascii_content(self):
        extractor = SnippetTextExtractor()

        # Both text and title unicode
        resource_info = ResourceInfo(
            metadata={'title': u'B\xe4ren'},
            text=u'B\xe4rengraben',
            headers={})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'graben', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

        # Both text and title utf-8
        resource_info = ResourceInfo(
            metadata={'title': 'B\xc3\xa4ren'},
            text='B\xc3\xa4rengraben',
            headers={})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'graben', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

        # Mix of unicode and utf-8
        resource_info = ResourceInfo(
            metadata={'title': u'B\xe4ren'},
            text='B\xc3\xa4rengraben',
            headers={})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'graben', extracted_value)
        self.assertIsInstance(extracted_value, unicode)


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


class TestFilenameExtractor(CrawlerTestCase):

    def test_extracts_filename_from_content_disposition(self):
        extractor = FilenameExtractor()
        resource_info = ResourceInfo(
            headers={'content-disposition': 'attachment; '
                     'filename="document.pdf"'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'document.pdf', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_raises_if_no_content_disposition_header(self):
        extractor = FilenameExtractor()
        resource_info = ResourceInfo(headers={})

        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)

    def test_raises_if_header_but_no_filename(self):
        extractor = FilenameExtractor()
        resource_info = ResourceInfo(headers={'content-disposition': ''})

        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestKeywordsExtractor(CrawlerTestCase):

    def test_extracts_comma_separated_keywords(self):
        extractor = KeywordsExtractor()
        resource_info = ResourceInfo(
            metadata={'keywords': 'Foo, Bar,     Baz'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals([u'Foo', u'Bar', u'Baz'], extracted_value)
        for item in extracted_value:
            self.assertIsInstance(item, unicode)

    def test_extracts_whitespace_separated_keywords(self):
        extractor = KeywordsExtractor()
        resource_info = ResourceInfo(metadata={'keywords': u'Foo Bar     Baz'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals([u'Foo', u'Bar', u'Baz'], extracted_value)
        for item in extracted_value:
            self.assertIsInstance(item, unicode)

    def test_raises_if_no_value_found(self):
        extractor = KeywordsExtractor()
        resource_info = ResourceInfo(metadata={})
        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestUIDExtractor(CrawlerTestCase):

    def test_builds_uid_based_on_url(self):
        extractor = UIDExtractor()
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'dab521de-65f9-250b-4cca-7383feef67dc',
                          extracted_value)
        self.assertIsInstance(extracted_value, unicode)

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


class TestSlugExtractor(CrawlerTestCase):

    def test_equals_basename_for_simple_urls(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/foo/bar'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'bar', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_deals_with_trailing_slash(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/foo/bar/'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'bar', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_defaults_to_index_html_for_empty_basename(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'index-html', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_deals_with_url_encoding(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/foo%%20bar'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'foo-bar', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_deals_with_non_ascii_characters_utf8(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': 'http://example.org/b\xc3\xa4rengraben'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'barengraben', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_deals_with_non_ascii_characters_unicode(self):
        extractor = SlugExtractor()
        resource_info = ResourceInfo(
            url_info={'loc': u'http://example.org/b\xe4rengraben'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'barengraben', extracted_value)
        self.assertIsInstance(extracted_value, unicode)


class TestURLExtractor(CrawlerTestCase):

    def test_extracts_url_from_urlinfo(self):
        extractor = URLExtractor()
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'http://example.org', extracted_value)
        self.assertIsInstance(extracted_value, unicode)


class TestTargetURLExtractor(CrawlerTestCase):

    def test_extracts_target_url_from_urlinfo(self):
        extractor = TargetURLExtractor()
        resource_info = ResourceInfo(url_info={
            'loc': 'http://example.org',
            'target': 'http://example.org/target',
        })
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'http://example.org/target', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_defaults_to_loc_if_no_target_given(self):
        extractor = TargetURLExtractor()
        resource_info = ResourceInfo(url_info={'loc': 'http://example.org'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'http://example.org', extracted_value)
        self.assertIsInstance(extracted_value, unicode)


class TestConstantExtractor(CrawlerTestCase):

    def test_returns_constant_value(self):
        extractor = ConstantExtractor(42)
        field = Field('example', extractor)
        extractor.bind(field)
        resource_info = ResourceInfo()

        self.assertEquals(42, extractor.extract_value(resource_info))

    def test_returns_unicode_for_string_constant(self):
        extractor = ConstantExtractor('foo')
        field = Field('example', extractor)
        extractor.bind(field)
        resource_info = ResourceInfo()
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'foo', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_returns_unicode_for_multivalued_string_constant(self):
        extractor = ConstantExtractor(['foo', 'bar'])
        field = Field('example', extractor, multivalued=True)
        extractor.bind(field)
        resource_info = ResourceInfo()
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals([u'foo', u'bar'], extracted_value)
        for item in extracted_value:
            self.assertIsInstance(item, unicode)


class TestIndexingTimeExtractor(DatetimeTestCase):

    def test_returns_current_time(self):
        extractor = IndexingTimeExtractor()
        resource_info = ResourceInfo()
        self.assertDatetimesAlmostEqual(
            datetime.utcnow(),
            extractor.extract_value(resource_info))


class TestSiteAttributeExtractor(CrawlerTestCase):

    def test_retrieves_attribute_from_site(self):
        site = Site('http://example.org', attributes={'name': 'My Site'})
        extractor = SiteAttributeExtractor('name')
        resource_info = ResourceInfo(site=site)

        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals(u'My Site', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_raises_if_attribute_not_found(self):
        site = Site('http://example.org')
        extractor = SiteAttributeExtractor('name')
        resource_info = ResourceInfo(site=site)

        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)


class TestHeaderMappingExtractor(CrawlerTestCase):

    def test_maps_header_to_value(self):
        mapping = {'text/html': 'HTML', 'image/png': 'IMAGE'}
        extractor = HeaderMappingExtractor('content-type', mapping)

        resource_info = ResourceInfo(headers={'content-type': 'text/html'})
        extracted_value = extractor.extract_value(resource_info)
        self.assertEquals('HTML', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

        resource_info = ResourceInfo(headers={'content-type': 'image/png'})
        extracted_value = extractor.extract_value(resource_info)
        self.assertEquals('IMAGE', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_uses_default_if_header_not_found(self):
        extractor = HeaderMappingExtractor(
            'content-type', {}, default='DEFAULT')
        resource_info = ResourceInfo(headers={})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals('DEFAULT', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_uses_default_if_header_not_mapped(self):
        extractor = HeaderMappingExtractor(
            'pragma', {}, default='DEFAULT')
        resource_info = ResourceInfo(headers={'pragma': 'no-cache'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals('DEFAULT', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_raises_if_no_default_and_header_not_found(self):
        extractor = HeaderMappingExtractor('content-type', {})
        resource_info = ResourceInfo(headers={})

        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)

    def test_raises_if_no_default_and_header_not_mapped(self):
        extractor = HeaderMappingExtractor('content-type', {})
        resource_info = ResourceInfo(headers={'content-type': 'text/html'})

        with self.assertRaises(NoValueExtracted):
            extractor.extract_value(resource_info)

    def test_deals_with_charset_in_content_type_header(self):
        mapping = {'text/html': 'HTML'}
        extractor = HeaderMappingExtractor('content-type', mapping)
        resource_info = ResourceInfo(
            headers={'content-type': 'text/html; charset=utf-8'})
        extracted_value = extractor.extract_value(resource_info)

        self.assertEquals('HTML', extracted_value)
        self.assertIsInstance(extracted_value, unicode)


class TestFieldMappingExtractor(CrawlerTestCase):

    def setUp(self):
        CrawlerTestCase.setUp(self)
        # TODO: Refactor this testcase
        site = Site('http://example.org')
        self.resource_info = ResourceInfo()
        self.mapping = {'travel': 'TRAVEL', 'music': 'MUSIC'}

        subcategory = Field(
            'subcategory',
            extractor=ConstantExtractor('travel'))

        category = Field(
            'category',
            extractor=FieldMappingExtractor('subcategory', self.mapping))

        self.config = Config(
            sites=[site],
            tika=None,
            solr=None,
            unique_field=None,
            url_field=None,
            last_modified_field=None,

            fields=[category, subcategory],)

    def test_maps_field_to_value(self):
        extractor = self.config.get_field('category').extractor
        extracted_value = extractor.extract_value(self.resource_info)

        self.assertEquals(u'TRAVEL', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_raises_if_field_not_found(self):
        category = self.config.get_field('category')
        category.extractor = FieldMappingExtractor(
            'missing_field', self.mapping)
        category.extractor.bind(category)

        with self.assertRaises(NoSuchField):
            category.extractor.extract_value(self.resource_info)

    def test_uses_default_if_field_returns_none(self):
        category = self.config.get_field('category')
        category.extractor.default = 'DEFAULT'
        subcategory = self.config.get_field('subcategory')
        subcategory.extractor = ConstantExtractor(None)
        subcategory.extractor.bind(subcategory)
        extracted_value = category.extractor.extract_value(self.resource_info)

        self.assertEquals(u'DEFAULT', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_raises_if_no_default_and_field_doesnt_return_value(self):
        category = self.config.get_field('category')
        subcategory = self.config.get_field('subcategory')
        subcategory.extractor = ConstantExtractor(None)
        subcategory.extractor.bind(subcategory)

        with self.assertRaises(NoValueExtracted):
            category.extractor.extract_value(self.resource_info)

    def test_uses_default_if_field_value_not_mapped(self):
        category = self.config.get_field('category')
        category.extractor.default = 'DEFAULT'
        subcategory = self.config.get_field('subcategory')
        subcategory.extractor = ConstantExtractor('physics')
        subcategory.extractor.bind(subcategory)
        extracted_value = category.extractor.extract_value(self.resource_info)

        self.assertEquals(u'DEFAULT', extracted_value)
        self.assertIsInstance(extracted_value, unicode)

    def test_raises_if_no_default_and_field_value_not_mapped(self):
        category = self.config.get_field('category')
        subcategory = self.config.get_field('subcategory')
        subcategory.extractor = ConstantExtractor('physics')
        subcategory.extractor.bind(subcategory)

        with self.assertRaises(NoValueExtracted):
            category.extractor.extract_value(self.resource_info)
