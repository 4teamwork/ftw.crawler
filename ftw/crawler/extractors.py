from BeautifulSoup import UnicodeDammit
from datetime import datetime
from ftw.crawler.exceptions import ExtractionError
from ftw.crawler.exceptions import NoValueExtracted
from ftw.crawler.utils import from_iso_datetime
from ftw.crawler.utils import get_content_type
from ftw.crawler.utils import normalize_whitespace
from ftw.crawler.utils import safe_unicode
from ftw.crawler.xml_utils import MARKUP_TYPES
from ftw.crawler.xml_utils import remove_namespaces
from lxml import etree
from slugify import slugify
from urllib import unquote_plus
from urlparse import urlparse
from uuid import UUID
import hashlib
import logging
import lxml.html


log = logging.getLogger(__name__)


class Extractor(object):
    """Base class for all extractors.
    """

    def extract_value(self, resource_info):
        raise NotImplementedError

    def bind(self, field):
        self.field = field

    def __repr__(self):
        cls = self.__class__
        name = '.'.join((cls.__module__, cls.__name__))
        return "<{}>".format(name)


class MetadataExtractor(Extractor):
    """Base class for all extractors that extract structured metadata via Tika.
    """


class TextExtractor(Extractor):
    """Base class for all extractors that extract plain text via Tika.
    """


class TextFromMarkupExtractor(Extractor):
    """Base class for all extractors that extract text from markup content.
    """


class URLInfoExtractor(Extractor):
    """Base class for all extractors that extract data from the sitemap's
    <urlinfo /> structure.
    """


class HTTPHeaderExtractor(Extractor):
    """Base class for all extractors that extract data from the response's
    HTTP headers.
    """


class ResourceIndependentExtractor(Extractor):
    """Base class for all extractors that don't need any information from
    the resource whatsoever.
    """


class SiteConfigExtractor(Extractor):
    """Base class for all extractors that extract data based on the `Site`
    configuration object.
    """


class ExtractionEngine(object):

    extractor_types = (
        MetadataExtractor, TextExtractor, URLInfoExtractor,
        ResourceIndependentExtractor, SiteConfigExtractor, HTTPHeaderExtractor,
        TextFromMarkupExtractor
    )

    def __init__(self, config, resource_info, converter):
        self.config = config
        self.resource_info = resource_info

        self.resource_info.metadata = converter.extract_metadata(
            self.resource_info)

        self.resource_info.text = safe_unicode(converter.extract_text(
            self.resource_info))

    def _unkown_extractor_type(self, extractor):
        cls = extractor.__class__
        raise ExtractionError(
            "Unknown extractor type for '{}' - must inherit from at least one "
            "of {}. (Current base classes: {})".format(
                ExtractionEngine.extractor_types, cls, cls.__bases__))

    def _assert_proper_type(self, field, value, extractor):
        if field.multivalued:
            valid_type = all(isinstance(v, field.type_) for v in value)
        else:
            valid_type = isinstance(value, field.type_)
        if not valid_type:
            raise ExtractionError(
                "Invalid return value type '{}' for extractor {} and field "
                "{}. Return value was: {}".format(
                    type(value).__name__, extractor, field, repr(value)))

    def _get_field_default(self, field):
        type_ = field.type_
        if issubclass(type_, datetime):
            epoch = datetime.utcfromtimestamp(0)
            return epoch
        else:
            # Return zero value for the respective type by instantiating it
            return type_()

    def extract_field_values(self):
        field_values = {}
        for field in self.config.fields:
            extractor = field.extractor

            if not isinstance(extractor, ExtractionEngine.extractor_types):
                self._unkown_extractor_type(extractor)

            try:
                value = extractor.extract_value(self.resource_info)
            except NoValueExtracted:
                if field.required:
                    value = self._get_field_default(field)
                else:
                    # No value could be extracted, and field is not required,
                    # so we may skip this field
                    continue
            self._assert_proper_type(field, value, extractor)
            field_values.update({field.name: value})
        return field_values


class PlainTextExtractor(TextExtractor):

    def extract_value(self, resource_info):
        return normalize_whitespace(resource_info.text)


class UIDExtractor(URLInfoExtractor):

    def extract_value(self, resource_info):
        url = resource_info.url_info['loc']
        hash_ = hashlib.md5(url)
        uid = UUID(bytes=hash_.digest())
        return unicode(uid)


class SlugExtractor(URLInfoExtractor):

    def _make_slug(self, value):
        value = unquote_plus(value)
        if not isinstance(value, unicode):
            value = value.decode('utf-8')
        slug = slugify(value)
        return slug

    def extract_value(self, resource_info):
        url = resource_info.url_info.get('loc')
        path = urlparse(url).path.rstrip('/')
        basename = path.split('/')[-1]
        if basename == '':
            basename = 'index-html'
        slug = self._make_slug(basename)
        return safe_unicode(slug)


class URLExtractor(URLInfoExtractor):

    def extract_value(self, resource_info):
        url = resource_info.url_info.get('loc')
        return safe_unicode(url)


class TargetURLExtractor(URLInfoExtractor):

    def extract_value(self, resource_info):
        if 'target' in resource_info.url_info:
            return safe_unicode(resource_info.url_info['target'])
        else:
            return URLExtractor().extract_value(resource_info)


class TitleExtractor(MetadataExtractor, HTTPHeaderExtractor, URLInfoExtractor):

    def _extract_title(self, resource_info):
        # If present, X-Document-Title header takes precedence
        if 'X-Document-Title' in resource_info.headers:
            header_value = resource_info.headers['X-Document-Title']
            return header_value.decode('base64').decode('utf-8').strip()

        # Next, try to get title from a `div#content h1` element
        h1_extractor = XPathExtractor("//div[@id='content']/h1")
        try:
            value = h1_extractor.extract_value(resource_info)
            return value
        except NoValueExtracted:
            pass

        # Next, attempt to get a title from Tika metadata
        value = resource_info.metadata.get('title')

        if value is None:
            try:
                # Fall back to filename from Content-Disposition header
                value = FilenameExtractor().extract_value(resource_info)
            except NoValueExtracted:
                # As a last resort, use a slug built from the rightmost part
                # of the resource's URL
                value = SlugExtractor().extract_value(resource_info)

        return value

    def extract_value(self, resource_info):
        title = self._extract_title(resource_info)
        return normalize_whitespace(title)


class XPathExtractor(TextFromMarkupExtractor, URLInfoExtractor):

    def __init__(self, xpath):
        self.xpath = xpath

    def _sniff_encoding(self, resource_info):
        with open(resource_info.filename) as f:
            data = f.read()
            proposed = ["utf-8", "latin1"]
            converted = UnicodeDammit(data, proposed, isHTML=True)
        del data
        return converted.originalEncoding

    def _get_tree(self, resource_info, encoding):
        # Use HTMLParser for everything, even XML / XHTML.
        if encoding is not None:
            parser = lxml.html.HTMLParser(encoding=encoding)
        else:
            parser = lxml.html.HTMLParser()
        tree = etree.parse(resource_info.filename, parser)
        tree = remove_namespaces(tree)
        return tree

    def extract_value(self, resource_info):
        if not resource_info.content_type in MARKUP_TYPES:
            raise NoValueExtracted

        encoding = self._sniff_encoding(resource_info)

        tree = self._get_tree(resource_info, encoding)
        nodes = tree.xpath(self.xpath)

        if len(nodes) == 0:
            raise NoValueExtracted

        elif len(nodes) > 1:
            log.warn(
                "XPath expression '{}' returned {} results for document at "
                "{}, using only first one".format(
                    self.xpath, len(nodes), resource_info.url_info['loc']))

        target_node = nodes[0]
        text = target_node.text_content()

        if isinstance(text, etree._ElementUnicodeResult):
            text = unicode(text)
        elif isinstance(text, etree._ElementStringResult):
            text = text.decode(encoding)
        else:
            log.error(
                "Unexpected return type for xpath(), expected"
                "'_ElementUnicodeResult'. (Node: {})".format(target_node))
            raise NoValueExtracted

        return text


class DescriptionExtractor(MetadataExtractor):

    def extract_value(self, resource_info):
        value = resource_info.metadata.get('description')
        if value is None:
            raise NoValueExtracted
        return safe_unicode(value)


class CreatorExtractor(MetadataExtractor):

    def extract_value(self, resource_info):
        value = resource_info.metadata.get('creator')
        if value is None:
            raise NoValueExtracted
        return safe_unicode(value)


class SnippetTextExtractor(TextExtractor, MetadataExtractor,
                           HTTPHeaderExtractor):

    def _get_title(self, resource_info):
        extractor = TitleExtractor()
        title = extractor.extract_value(resource_info)
        return title.strip()

    def _get_plain_text(self, resource_info):
        extractor = PlainTextExtractor()
        plain_text = extractor.extract_value(resource_info)
        return plain_text.strip()

    def extract_value(self, resource_info):
        plain_text = safe_unicode(self._get_plain_text(resource_info))
        title = safe_unicode(self._get_title(resource_info))

        snippet_text = plain_text
        # strip title at start of plain text
        if title is not None and snippet_text.startswith(title):
            snippet_text = snippet_text.lstrip(title)
        return safe_unicode(snippet_text)


class LastModifiedExtractor(URLInfoExtractor, HTTPHeaderExtractor):

    def extract_value(self, resource_info):
        if 'lastmod' in resource_info.url_info:
            datestring = resource_info.url_info['lastmod']
            utc_dt = from_iso_datetime(datestring)
            return utc_dt

        if 'last-modified' in resource_info.headers:
            # TODO: We rely on requests.structures.CaseInsensitiveDict here
            utc_dt = from_iso_datetime(resource_info.headers['last-modified'])
            return utc_dt

        utc_dt = IndexingTimeExtractor().extract_value(resource_info)
        return utc_dt


class FilenameExtractor(HTTPHeaderExtractor):

    def extract_value(self, resource_info):
        if 'content-disposition' in resource_info.headers:
            # TODO: We rely on requests.structures.CaseInsensitiveDict here
            header_value = resource_info.headers['content-disposition']
            items = [i.strip() for i in header_value.split(';')]
            for item in items:
                if item.lower().startswith('filename'):
                    key, value = [token.strip() for token in item.split('=')]
                    filename = value.replace('"', '')
                    # TODO: Deal with encoding of non-ASCII filenames
                    return filename.decode('utf-8', errors='replace')
        raise NoValueExtracted


class KeywordsExtractor(MetadataExtractor):

    def extract_value(self, resource_info):
        value = resource_info.metadata.get('keywords')
        if value is None:
            raise NoValueExtracted
        if ',' in value:
            keywords = value.split(',')
        else:
            keywords = value.split()
        return [safe_unicode(kw.strip()) for kw in keywords]


class ConstantExtractor(ResourceIndependentExtractor):

    def __init__(self, value):
        self.value = value

    def extract_value(self, resource_info):
        value = self.value

        if isinstance(value, str):
            value = safe_unicode(value)

        if self.field.multivalued:
            value = [safe_unicode(v) for v in self.value]

        return value


class IndexingTimeExtractor(ResourceIndependentExtractor):

    def extract_value(self, resource_info):
        return datetime.utcnow()


class SiteAttributeExtractor(SiteConfigExtractor):

    def __init__(self, key):
        self.key = key

    def extract_value(self, resource_info):
        value = resource_info.site.attributes.get(self.key)

        if value is None:
            raise NoValueExtracted

        if isinstance(value, str):
            value = safe_unicode(value)

        return value


class HeaderMappingExtractor(HTTPHeaderExtractor):

    def __init__(self, header_name, mapping, default=None):
        self.header_name = header_name
        self.mapping = mapping
        self.default = default

    def _default_or_raise(self):
        if self.default is not None:
            return safe_unicode(self.default)
        else:
            raise NoValueExtracted

    def extract_value(self, resource_info):
        header_value = resource_info.headers.get(self.header_name)
        if header_value is None:
            # Header not present
            return self._default_or_raise()

        if self.header_name.lower() == 'content-type':
            header_value = get_content_type(header_value)

        if header_value in self.mapping:
            return safe_unicode(self.mapping[header_value])
        else:
            # Header present but not mapped
            return self._default_or_raise()


class FieldMappingExtractor(HTTPHeaderExtractor):

    def __init__(self, field_name, mapping, default=None):
        self.field_name = field_name
        self.mapping = mapping
        self.default = default

    def _default_or_raise(self):
        if self.default is not None:
            return safe_unicode(self.default)
        else:
            raise NoValueExtracted

    def extract_value(self, resource_info):
        mapped_field = self.field.config.get_field(self.field_name)
        field_value = mapped_field.extractor.extract_value(resource_info)
        if field_value is None:
            # Field not extracted
            return self._default_or_raise()

        if field_value in self.mapping:
            return safe_unicode(self.mapping[field_value])
        else:
            # Field present but not mapped
            return self._default_or_raise()
