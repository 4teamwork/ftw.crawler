import imp
import os


def get_config(args):
    config_path = os.path.abspath(args.config)
    module_name = os.path.splitext(os.path.basename(args.config))[0]
    module = imp.load_source(module_name, config_path)
    return module.CONFIG


class Config(object):

    def __init__(self, sites, tika, solr, fields):
        self.sites = sites
        self.tika = tika
        self.solr = solr
        self.fields = fields


class Site(object):

    def __init__(self, url, attributes=None):
        self.url = url

        if attributes is None:
            attributes = {}
        self.attributes = attributes


class Field(object):

    def __init__(self, name, extractor, type_=str, required=False,
                 multivalued=False):
        self.name = name
        self.extractor = extractor
        self.type_ = type_
        self.required = required
        self.multivalued = multivalued

    def __repr__(self):
        desc = "<Field '{}' type_={} required={} multivalued={} extractor={}>"
        return desc.format(
            self.name, self.type_.__name__, self.required, self.multivalued,
            self.extractor)
