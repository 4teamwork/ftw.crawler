from ftw.crawler.exceptions import FetchingError
from ftw.crawler.utils import get_content_type
import tempfile


class ResourceFetcher(object):

    def __init__(self, resource_info, session, tempdir):
        self.resource_info = resource_info
        self.session = session
        self.tempdir = tempdir

    def _mktmp(self):
        return tempfile.NamedTemporaryFile(dir=self.tempdir, delete=False)

    def fetch(self):
        resource_info = self.resource_info
        url = resource_info.url_info['loc']

        response = self.session.get(url)
        if not response.status_code == 200:
            raise FetchingError("Could not fetch {}. Got status {}".format(
                url, response.status_code))

        with self._mktmp() as resource_file:
            resource_file.write(response.content)

        content_type = get_content_type(response.headers.get('Content-Type'))

        resource_info.filename = resource_file.name
        resource_info.content_type = content_type
        resource_info.headers = response.headers
        resource_info.filename = resource_file.name

        return resource_info
