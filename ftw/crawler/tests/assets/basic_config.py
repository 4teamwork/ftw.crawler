from datetime import datetime
from ftw.crawler.configuration import Config
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import Site
from ftw.crawler.extractors import ConstantExtractor
from ftw.crawler.extractors import CreatorExtractor
from ftw.crawler.extractors import DescriptionExtractor
from ftw.crawler.extractors import FieldMappingExtractor
from ftw.crawler.extractors import HeaderMappingExtractor
from ftw.crawler.extractors import IndexingTimeExtractor
from ftw.crawler.extractors import KeywordsExtractor
from ftw.crawler.extractors import LastModifiedExtractor
from ftw.crawler.extractors import PlainTextExtractor
from ftw.crawler.extractors import SiteAttributeExtractor
from ftw.crawler.extractors import SlugExtractor
from ftw.crawler.extractors import SnippetTextExtractor
from ftw.crawler.extractors import TargetURLExtractor
from ftw.crawler.extractors import TitleExtractor
from ftw.crawler.extractors import UIDExtractor
from ftw.crawler.extractors import URLExtractor


PORTAL_TYPE_MAPPING = {
    'text/html': 'ContentPage',
    'application/pdf': 'File',
}

OBJECT_TYPE_MAPPING = {
    'ContentPage': 'CONTENT_PAGE',
    'File': 'FILE',
}


# May be overriden via command line arguments
TIKA_URL = 'http://localhost:9998/'
SOLR_URL = 'http://localhost:8983/solr'


CONFIG = Config(
    sites=[
        Site('https://www.sportamt-bern.ch/',
             attributes={'site_area': 'Sportamt Bern'}),

        Site('http://www.sitemapxml.co.uk/',
             attributes={'site_area': 'Sitemap XML'}),

        Site('http://www.pctipp.ch/',
             attributes={'site_area': 'PCtipp'}),

        Site('http://mailchimp.com',
             attributes={'site_area': 'MailChimp'}),

        Site('https://bgs.zg.ch',
             attributes={'site_area': 'Gesetzessammlung'}),
    ],
    unique_field='UID',
    url_field='path_string',
    last_modified_field='modified',

    fields=[
        Field('allowedRolesAndUsers',
              extractor=ConstantExtractor(['Anonymous']),
              multivalued=True),
        Field('created',
              extractor=LastModifiedExtractor(),
              type_=datetime),
        Field('Creator',
              extractor=CreatorExtractor()),
        Field('Description',
              extractor=DescriptionExtractor()),
        Field('effective',
              extractor=IndexingTimeExtractor(),
              type_=datetime),
        Field('expires',
              extractor=ConstantExtractor(datetime(2050, 12, 31)),
              type_=datetime),
        Field('getId',
              extractor=SlugExtractor()),
        Field('getRemoteUrl',
              extractor=TargetURLExtractor()),
        Field('modified',
              extractor=LastModifiedExtractor(),
              type_=datetime),
        Field('object_type',
              extractor=FieldMappingExtractor(
                  'portal_type', OBJECT_TYPE_MAPPING, default='File')),
        Field('path_string',
              extractor=URLExtractor()),
        Field('portal_type',
              extractor=HeaderMappingExtractor(
                  'content-type', PORTAL_TYPE_MAPPING, default='File')),
        Field('SearchableText',
              extractor=PlainTextExtractor()),
        Field('showinsearch',
              extractor=ConstantExtractor(True),
              type_=bool),
        Field('site_area',
              extractor=SiteAttributeExtractor('site_area'),
              multivalued=True),
        Field('snippetText',
              extractor=SnippetTextExtractor()),
        Field('Subject',
              extractor=KeywordsExtractor(),
              multivalued=True),
        Field('Title',
              extractor=TitleExtractor()),
        Field('topics',
              extractor=KeywordsExtractor(),
              multivalued=True),
        Field('UID',
              extractor=UIDExtractor(),
              required=True),
    ],
    tika=TIKA_URL,
    solr=SOLR_URL,
)
