from ftw.crawler.exceptions import FetchingError
import requests


class ResourceFetcher(object):

    def __init__(self, url_info, resource_file):
        self.url_info = url_info
        self.resource_file = resource_file

    def fetch(self):
        url = self.url_info['loc']
        response = requests.get(url)
        if not response.status_code == 200:
            raise FetchingError("Could not fetch {}. Got status {}".format(
                url, response.status_code))

        try:
            self.resource_file.seek(0)
            self.resource_file.write(response.content)
        finally:
            self.resource_file.close()

        content_type = response.headers.get('Content-Type')
        return self.resource_file.name, content_type
