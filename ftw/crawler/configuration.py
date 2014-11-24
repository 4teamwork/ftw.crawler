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

    def __init__(self, url):
        self.url = url


class Field(object):

    def __init__(self, name, extractors, type_):
        self.name = name
        self.extractors = extractors
        self.type_ = type_
