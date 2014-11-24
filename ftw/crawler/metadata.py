METADATA_MAPPING = {
    'title': ['dcterms:title', 'dc:title', 'title'],
    'created': ['dcterms:created', 'meta:creation-date', 'Creation-Date'],
}


class SimpleMetadata(dict):
    """A dict subclass to map prefixed metadata properties from different
    metadata sets to common, canonical keys.

    E.g. the value for key 'dcterms:title' will be mapped to just 'title'.

    Prefixes take precedence in the order they are specified, i.e. the first
    prefix that is found will be mapped to the canonical key and the search is
    then stopped.
    """

    def __init__(self, mapping):
        dict.__init__(self, mapping)

        simple_metadata = {}
        for property_, keys in METADATA_MAPPING.items():
            for possible_key in keys:
                if possible_key in self:
                    simple_metadata[property_] = self[possible_key]
                    break

        self.update(simple_metadata)
