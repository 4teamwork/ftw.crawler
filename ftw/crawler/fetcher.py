from ftw.crawler.exceptions import AttemptedRedirect
from ftw.crawler.exceptions import FetchingError
from ftw.crawler.exceptions import NotModified
from ftw.crawler.utils import from_iso_datetime
from ftw.crawler.utils import get_content_type
import logging
import tempfile
import time


log = logging.getLogger(__name__)


class ResourceFetcher(object):

    def __init__(self, resource_info, session, tempdir, options):
        self.resource_info = resource_info
        self.url_info = resource_info.url_info
        self.session = session
        self.tempdir = tempdir
        self.options = options

    def _mktmp(self):
        return tempfile.NamedTemporaryFile(dir=self.tempdir, delete=False)

    def is_modified(self):
        if self.resource_info.last_indexed is None:
            return True

        if 'lastmod' in self.url_info:
            last_modified = self.url_info['lastmod']
            last_modified = from_iso_datetime(last_modified)
            return last_modified > self.resource_info.last_indexed

        # No 'lastmod' in urlinfo - fall back to a HEAD request
        response = self.session.head(self.url_info['loc'])
        if 'last-modified' in response.headers:
            # TODO: Use 'closing' context manager in order to avoid
            # blocking connection pool
            last_modified = response.headers['last-modified']
            last_modified = from_iso_datetime(last_modified)
            return last_modified > self.resource_info.last_indexed
        return True

    def fetch(self):
        resource_info = self.resource_info
        url = self.url_info['loc']

        modified = self.is_modified()
        if not self.options.force and not modified:
            raise NotModified

        response = self.session.get(url, allow_redirects=False)
        if response.is_redirect:
            # TODO: With redirects it's unclear which URL to use as the
            # canonical URL - so we don't allow them for now.
            log.warn(u"URL {} attempted a redirect - skipped.".format(url))
            raise AttemptedRedirect(url)

        while response.status_code == 429:
            log.warn(u"429 Too Many Requests, sleeping for {}s".format(
                self.resource_info.site.sleeptime))
            time.sleep(self.resource_info.site.sleeptime)
            response = self.session.get(url, allow_redirects=False)
            if response.status_code == 429:
                self.resource_info.site.sleeptime *= 2

        if not response.status_code == 200:
            raise FetchingError(u"Could not fetch {}. Got status {}".format(
                url, response.status_code))

        with self._mktmp() as resource_file:
            resource_file.write(response.content)

        content_type = get_content_type(response.headers.get('Content-Type'))

        resource_info.filename = resource_file.name
        resource_info.content_type = content_type
        resource_info.headers = response.headers
        resource_info.filename = resource_file.name

        log.debug(u"Resource saved to {}".format(resource_info.filename))
        return resource_info
