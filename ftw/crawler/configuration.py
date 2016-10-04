from ftw.crawler.exceptions import NoSuchField
from ftw.crawler.exceptions import SiteNotFound
import imp
import os


def get_config(options):
    config_path = os.path.abspath(options.config)
    module_name = os.path.splitext(os.path.basename(options.config))[0]
    module = imp.load_source(module_name, config_path)
    config = module.CONFIG

    # Command line options for Tika and Solr override config values
    if options.tika:
        config.tika = options.tika
    if options.solr:
        config.solr = options.solr

    if not (config.tika and config.solr):
        raise ValueError(
            'Tika and Solr URLs must be specified, either via command line '
            'arguments or parameters in the configuration file.')

    return module.CONFIG


class Config(object):

    def __init__(self, sites, unique_field, url_field, last_modified_field,
                 fields, tika=None, solr=None):
        self.sites = sites
        self.unique_field = unique_field
        self.url_field = url_field
        self.last_modified_field = last_modified_field
        self.fields = fields
        self.tika = tika
        self.solr = solr

        for site in self.sites:
            site.bind(self)

        for field in self.fields:
            field.bind(self)

    def get_field(self, field_name):
        for field in self.fields:
            if field.name == field_name:
                return field
        raise NoSuchField(field_name)

    def get_site(self, url):
        for site in self.sites:
            if site.url == url:
                return site
        raise SiteNotFound("Couldn't find site %r in config!" % url)


class Site(object):

    def __init__(self, url, attributes=None, sleeptime=0.1):
        self.url = url
        self.sleeptime = sleeptime

        if attributes is None:
            attributes = {}
        self.attributes = attributes

    def bind(self, config):
        self.config = config


class Field(object):

    def __init__(self, name, extractor, type_=unicode, required=False,
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
