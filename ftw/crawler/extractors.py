class Extractor(object):
    """Base class for all extractors.
    """


class MetadataExtractor(Extractor):
    """Base class for all extractors that extract structured metadata via Tika.
    """

    def extract_metadata(self, metadata):
        raise NotImplementedError


class TextExtractor(Extractor):
    """Base class for all extractors that extract plain text via Tika.
    """

    def extract_text(self, text):
        raise NotImplementedError


class ExtractionEngine(object):

    def __init__(self, config, fileobj, content_type, filename,
                 fields, converter):
        self.config = config
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
            "Unknown extractor type for '{}' - must inherit from either "
            "MetadataExtractor or TextExtractor. "
            "(Base classes: {})".format(cls, cls.__bases__))

    def extract_field_values(self):
        field_values = {}
        for field in self.fields:
            for extractor in field.extractors:
                if isinstance(extractor, MetadataExtractor):
                    value = extractor.extract_metadata(self.metadata)
                elif isinstance(extractor, TextExtractor):
                    value = extractor.extract_text(self.text)
                else:
                    self._unkown_extractor_type(extractor)
                assert isinstance(value, field.type_)
                field_values.update({field.name: value})
        return field_values


class PlainTextExtractor(TextExtractor):

    def extract_text(self, text):
        return text


class TitleExtractor(MetadataExtractor):

    def extract_metadata(self, metadata):
        return metadata.get('title')
