from uuid import UUID
import hashlib


class Extractor(object):
    """Base class for all extractors.
    """
    def extract_value(self):
        raise NotImplementedError


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


class ExtractionEngine(object):

    extractor_types = (MetadataExtractor, TextExtractor, URLInfoExtractor)

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
        raise TypeError(
            "Unknown extractor type for '{}' - must inherit from at least one "
            "of {}. (Current base classes: {})".format(
                ExtractionEngine.extractor_types, cls, cls.__bases__))

    def extract_field_values(self):
        field_values = {}
        for field in self.fields:
            for extractor in field.extractors:
                if isinstance(extractor, MetadataExtractor):
                    extractor.metadata = self.metadata
                if isinstance(extractor, TextExtractor):
                    extractor.text = self.text
                if isinstance(extractor, URLInfoExtractor):
                    extractor.url_info = self.url_info

                if not isinstance(extractor, ExtractionEngine.extractor_types):
                    self._unkown_extractor_type(extractor)

                value = extractor.extract_value()
                assert isinstance(value, field.type_)
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
        return self.metadata.get('title')
