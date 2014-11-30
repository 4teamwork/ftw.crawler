from ftw.crawler.metadata import SimpleMetadata
import csv
import io
import logging
import requests


log = logging.getLogger(__name__)


class TikaConverter(object):

    def __init__(self, tika_url):
        self.tika_url = tika_url.rstrip('/')

    def _tika_request(self, endpoint, resource_info, headers):
        tika_endpoint = '/'.join((self.tika_url, endpoint))
        with open(resource_info.filename) as fileobj:
            response = requests.put(
                tika_endpoint, data=fileobj, headers=headers)
        return response

    def extract_metadata(self, resource_info):
        log.info("Extracting metadata from '{}' with "
                 "tika JAXRS server.".format(resource_info.filename))

        headers = {'Content-type': resource_info.content_type}
        response = self._tika_request('meta', resource_info, headers)

        csv_file = io.BytesIO(response.content)
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        metadata = dict(iter(csv_reader))
        return SimpleMetadata(metadata)

    def extract_text(self, resource_info):
        log.info("Extracting plain text from '{}' with "
                 "tika JAXRS server.".format(resource_info.filename))

        headers = {'Content-type': resource_info.content_type,
                   'Accept': 'text/plain'}
        response = self._tika_request('tika', resource_info, headers)
        return response.content
