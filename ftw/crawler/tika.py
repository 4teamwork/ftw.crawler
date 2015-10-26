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
        log.debug(u"Extracting metadata from '{}' with "
                  "tika JAXRS server.".format(resource_info.filename))

        headers = {'Content-type': resource_info.content_type}
        response = self._tika_request('meta', resource_info, headers)

        csv_file = io.BytesIO(response.content)
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')

        metadata = {}
        for item in iter(csv_reader):
            # In rare cases, Tika returns more than one value per key. So we
            # just join everything after the key using a space, which won't
            # change anything for 99% of items that are just key/value pairs.
            key = item[0]
            value = ' '.join(item[1:])
            metadata[key] = value

        # TODO: We assume Tika returns utf-8 encoded metadata
        for key, value in metadata.items():
            metadata[key] = value.decode('utf-8')

        return SimpleMetadata(metadata)

    def extract_text(self, resource_info):
        log.debug(u"Extracting plain text from '{}' with "
                  "tika JAXRS server.".format(resource_info.filename))

        headers = {'Content-type': resource_info.content_type,
                   'Accept': 'text/plain'}
        response = self._tika_request('tika', resource_info, headers)

        # Normally we would just use response.text to get the decoded response
        # body in unicode, but Tika uses UTF-8 *without declaring it*.
        # See https://issues.apache.org/jira/browse/TIKA-912
        return response.content.decode('utf-8')
