from ftw.crawler.utils import get_content_type
from unittest2 import TestCase


class TestGetContentType(TestCase):

    def test_strips_charset(self):
        header_value = 'text/html; charset=utf-8'
        self.assertEquals('text/html', get_content_type(header_value))

    def test_also_works_for_mimetype_only(self):
        header_value = 'text/html'
        self.assertEquals('text/html', get_content_type(header_value))
