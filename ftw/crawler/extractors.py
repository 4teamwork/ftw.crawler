from datetime import datetime
from ftw.crawler.exceptions import ExtractionError
from ftw.crawler.exceptions import NoValueExtracted
from uuid import UUID
import hashlib


class Extractor(object):
    """Base class for all extractors.
    """
    def extract_value(self):
        raise NotImplementedError

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


class ResourceIndependentExtractor(Extractor):
    """Base class for all extractors that don't need any information from
    the resource whatsoever.
    """


class ExtractionEngine(object):

    extractor_types = (
        MetadataExtractor, TextExtractor, URLInfoExtractor,
        ResourceIndependentExtractor
    )

    def __init__(self, config, url_info, fileobj, content_type, filename,
                 fields, converter):
        self.config = config
        self.url_info = url_info
        self.fileobj = fileobj
        self.content_type = content_type
        self.filename = filename
        self.fields = fields

        self.metadata = converter.extract_metadata(
            self.fileobj, self.content_type, self.filename)

        self.text = converter.extract_text(
            self.fileobj, self.content_type, self.filename)

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
        for field in self.fields:
            extractor = field.extractor
            if isinstance(extractor, MetadataExtractor):
                extractor.metadata = self.metadata
            if isinstance(extractor, TextExtractor):
                extractor.text = self.text
            if isinstance(extractor, URLInfoExtractor):
                extractor.url_info = self.url_info

            if not isinstance(extractor, ExtractionEngine.extractor_types):
                self._unkown_extractor_type(extractor)

            try:
                value = extractor.extract_value()
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

    def extract_value(self):
        return self.text


class UIDExtractor(URLInfoExtractor):

    def extract_value(self):
        url = self.url_info['loc']
        hash_ = hashlib.md5(url)
        uid = UUID(bytes=hash_.digest())
        return str(uid)


class URLExtractor(URLInfoExtractor):

    def extract_value(self):
        return self.url_info.get('loc')


class TitleExtractor(MetadataExtractor):

    def extract_value(self):
        value = self.metadata.get('title')
        if value is None:
            raise NoValueExtracted
        return value


class DescriptionExtractor(MetadataExtractor):

    def extract_value(self):
        value = self.metadata.get('description')
        if value is None:
            raise NoValueExtracted
        return value


class ConstantExtractor(ResourceIndependentExtractor):

    def __init__(self, value):
        self.value = value

    def extract_value(self):
        return self.value


class IndexingTimeExtractor(ResourceIndependentExtractor):

    def extract_value(self):
        return datetime.utcnow()
