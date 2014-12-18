from pkg_resources import resource_string
import json


def get_asset(filename):
    return resource_string('ftw.crawler.tests.assets', filename)


class MockRequest(object):

    def __init__(self, url='http://example.org'):
        self.url = url


class MockResponse(object):

    def __init__(self, content=None, status_code=200, headers=None,
                 request=None, is_redirect=False):
        self.content = content
        self.status_code = status_code

        if headers is None:
            headers = {}
        self.headers = headers

        if request is None:
            request = MockRequest()
        self.request = request

        self.is_redirect = is_redirect

    @property
    def text(self):
        return self.content.decode('utf-8')

    def json(self):
        return json.loads(self.content)


class MockConverter(object):

    def __init__(self, metadata=None, text=''):
        if metadata is None:
            metadata = {}
        self.metadata = metadata

        self.text = text

    def extract_metadata(self, resource_info):
        return self.metadata

    def extract_text(self, resource_info):
        return self.text
