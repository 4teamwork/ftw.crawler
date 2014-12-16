from ftw.crawler.metadata import SimpleMetadata
from ftw.crawler.testing import CrawlerTestCase


class TestSimpleMetadata(CrawlerTestCase):

    def test_original_prefixed_entries_are_preserved(self):
        metadata = {'dcterms:title': 'My Title'}
        simple_metadata = SimpleMetadata(metadata)
        self.assertEquals('My Title', simple_metadata['dcterms:title'])

    def test_handles_dcterms_title(self):
        metadata = {'dcterms:title': 'My Title'}
        simple_metadata = SimpleMetadata(metadata)
        self.assertEquals('My Title', simple_metadata['title'])

    def test_handles_dc_title(self):
        metadata = {'dc:title': 'My Title'}
        simple_metadata = SimpleMetadata(metadata)
        self.assertEquals('My Title', simple_metadata['title'])

    def test_handles_dcterms_take_precedence_over_dc(self):
        metadata = {'dc:title': 'Some irrelevant Title',
                    'dcterms:title': 'My Title'}
        simple_metadata = SimpleMetadata(metadata)
        self.assertEquals('My Title', simple_metadata['title'])
