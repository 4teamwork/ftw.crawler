import json
from pkg_resources import resource_string


def get_config():
    config = json.loads(resource_string(
        'ftw.crawler.examples', 'config.json'))
    return config
