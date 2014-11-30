from datetime import datetime
from ftw.crawler.exceptions import ExtractionError
from ftw.crawler.exceptions import NoValueExtracted
from ftw.crawler.utils import from_iso_datetime
from ftw.crawler.utils import get_content_type
from slugify import slugify
from urllib import unquote_plus
from urlparse import urlparse
from uuid import UUID
import hashlib


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
        ResourceIndependentExtractor, SiteConfigExtractor, HTTPHeaderExtractor
    )

    def __init__(self, config, resource_info, converter):
        self.config = config
        self.resource_info = resource_info

        self.resource_info.metadata = converter.extract_metadata(
            self.resource_info)

        self.resource_info.text = converter.extract_text(
            self.resource_info)

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
        return resource_info.text


class UIDExtractor(URLInfoExtractor):

    def extract_value(self, resource_info):
        url = resource_info.url_info['loc']
        hash_ = hashlib.md5(url)
        uid = UUID(bytes=hash_.digest())
        return str(uid)


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
        return slug


class URLExtractor(URLInfoExtractor):

    def extract_value(self, resource_info):
        return resource_info.url_info.get('loc')


class TitleExtractor(MetadataExtractor):

    def extract_value(self, resource_info):
        value = resource_info.metadata.get('title')
        if value is None:
            raise NoValueExtracted
        return value


class DescriptionExtractor(MetadataExtractor):

    def extract_value(self, resource_info):
        value = resource_info.metadata.get('description')
        if value is None:
            raise NoValueExtracted
        return value


class CreatorExtractor(MetadataExtractor):

    def extract_value(self, resource_info):
        value = resource_info.metadata.get('creator')
        if value is None:
            raise NoValueExtracted
        return value


class SnippetTextExtractor(TextExtractor, MetadataExtractor):

    def _get_title(self, resource_info):
        extractor = TitleExtractor()
        try:
            title = extractor.extract_value(resource_info)
        except NoValueExtracted:
            return None
        return title.strip()

    def _get_plain_text(self, resource_info):
        extractor = PlainTextExtractor()
        plain_text = extractor.extract_value(resource_info)
        return plain_text.strip()

    def extract_value(self, resource_info):
        plain_text = self._get_plain_text(resource_info)
        title = self._get_title(resource_info)

        snippet_text = plain_text
        # strip title at start of plain text
        if title is not None and snippet_text.startswith(title):
            snippet_text = snippet_text.lstrip(title).strip()
        return snippet_text


class LastModifiedExtractor(URLInfoExtractor, HTTPHeaderExtractor):

    def extract_value(self, resource_info):
        if 'lastmod' in resource_info.url_info:
            datestring = resource_info.url_info['lastmod']
            print datestring
            utc_dt = from_iso_datetime(datestring)
            return utc_dt

        if 'last-modified' in resource_info.headers:
            # TODO: We rely on requests.structures.CaseInsensitiveDict here
            utc_dt = from_iso_datetime(resource_info.headers['last-modified'])
            return utc_dt

        utc_dt = IndexingTimeExtractor().extract_value(resource_info)
        return utc_dt


class KeywordsExtractor(MetadataExtractor):

    def extract_value(self, resource_info):
        value = resource_info.metadata.get('keywords')
        if value is None:
            raise NoValueExtracted
        if ',' in value:
            keywords = value.split(',')
        else:
            keywords = value.split()
        return [kw.strip() for kw in keywords]


class ConstantExtractor(ResourceIndependentExtractor):

    def __init__(self, value):
        self.value = value

    def extract_value(self, resource_info):
        return self.value


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
        return value


class HeaderMappingExtractor(HTTPHeaderExtractor):

    def __init__(self, header_name, mapping, default=None):
        self.header_name = header_name
        self.mapping = mapping
        self.default = default

    def _default_or_raise(self):
        if self.default is not None:
            return self.default
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
            return self.mapping[header_value]
        else:
            # Header present but not mapped
            return self._default_or_raise()
