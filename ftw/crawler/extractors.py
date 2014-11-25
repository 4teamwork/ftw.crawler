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


class ExtractionEngine(object):

    extractor_types = (MetadataExtractor, TextExtractor)

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
                    extractor.metadata = self.metadata
                if isinstance(extractor, TextExtractor):
                    extractor.text = self.text

                if not isinstance(extractor, ExtractionEngine.extractor_types):
                    self._unkown_extractor_type(extractor)

                value = extractor.extract_value()
                assert isinstance(value, field.type_)
                field_values.update({field.name: value})
        return field_values


class PlainTextExtractor(TextExtractor):

    def extract_value(self):
        return self.text


class TitleExtractor(MetadataExtractor):

    def extract_value(self):
        return self.metadata.get('title')
