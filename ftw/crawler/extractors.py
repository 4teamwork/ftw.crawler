class Extractor(object):
    """Base class for all extractors.
    """


class MetadataExtractor(Extractor):
    """Base class for all extractors that extract structured metadata via Tika.
    """

    def extract_metadata(self, metadata):
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

    def extract_field_values(self):
        field_values = {}
        for field in self.fields:
            for extractor in field.extractors:
                value = extractor.extract_metadata(self.metadata)
                assert isinstance(value, field.type_)
                field_values.update({field.name: value})
        return field_values


class TitleExtractor(MetadataExtractor):

    def extract_metadata(self, metadata):
        return metadata.get('title')
