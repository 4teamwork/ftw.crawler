from datetime import datetime
from ftw.crawler.configuration import Config
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import Site
from ftw.crawler.extractors import ConstantExtractor
from ftw.crawler.extractors import CreatorExtractor
from ftw.crawler.extractors import DescriptionExtractor
from ftw.crawler.extractors import IndexingTimeExtractor
from ftw.crawler.extractors import KeywordsExtractor
from ftw.crawler.extractors import LastModifiedExtractor
from ftw.crawler.extractors import PlainTextExtractor
from ftw.crawler.extractors import SiteAttributeExtractor
from ftw.crawler.extractors import SlugExtractor
from ftw.crawler.extractors import SnippetTextExtractor
from ftw.crawler.extractors import TitleExtractor
from ftw.crawler.extractors import UIDExtractor
from ftw.crawler.extractors import URLExtractor


CONFIG = Config(
    sites=[
        Site('http://www.sitemapxml.co.uk/',
             attributes={'site_area': 'Sitemap XML'}),

        Site('https://www.dropbox.com/',
             attributes={'site_area': 'Dropbox'}),

        Site('http://zg.clex.ch',
             attributes={'site_area': 'Gesetzessammlung'}),
    ],
    tika='http://localhost:9998/',
    solr='http://localhost:8983/solr',
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
              extractor=URLExtractor()),
        Field('modified',
              extractor=LastModifiedExtractor(),
              type_=datetime),
        Field('path_string',
              extractor=URLExtractor()),
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
    ]
)
