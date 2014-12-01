from ftw.crawler.exceptions import NoSuchField
import imp
import os


def get_config(args):
    config_path = os.path.abspath(args.config)
    module_name = os.path.splitext(os.path.basename(args.config))[0]
    module = imp.load_source(module_name, config_path)
    return module.CONFIG


class Config(object):

    def __init__(self, sites, tika, solr, unique_field, url_field,
                 last_modified_field, fields):
        self.sites = sites
        self.tika = tika
        self.solr = solr
        self.unique_field = unique_field
        self.url_field = url_field
        self.last_modified_field = last_modified_field
        self.fields = fields

        for site in self.sites:
            site.bind(self)

        for field in self.fields:
            field.bind(self)

    def get_field(self, field_name):
        for field in self.fields:
            if field.name == field_name:
                return field
        raise NoSuchField(field_name)


class Site(object):

    def __init__(self, url, attributes=None):
        self.url = url

        if attributes is None:
            attributes = {}
        self.attributes = attributes

    def bind(self, config):
        self.config = config


class Field(object):

    def __init__(self, name, extractor, type_=str, required=False,
                 multivalued=False):
        self.name = name
        self.extractor = extractor
        self.type_ = type_
        self.required = required
        self.multivalued = multivalued

        self.extractor.bind(self)

    def bind(self, config):
        self.config = config

    def __repr__(self):
        desc = "<Field '{}' type_={} required={} multivalued={} extractor={}>"
        return desc.format(
            self.name, self.type_.__name__, self.required, self.multivalued,
            self.extractor)
