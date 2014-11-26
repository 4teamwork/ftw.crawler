from datetime import datetime
from ftw.crawler.configuration import Config
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import Site
from ftw.crawler.extractors import ConstantExtractor
from ftw.crawler.extractors import IndexingTimeExtractor
from ftw.crawler.extractors import PlainTextExtractor
from ftw.crawler.extractors import TitleExtractor
from ftw.crawler.extractors import UIDExtractor
from ftw.crawler.extractors import URLExtractor


CONFIG = Config(
    sites=[
        Site('http://www.sitemapxml.co.uk/'),
        Site('https://www.dropbox.com/'),
        Site('http://zg.clex.ch'),
    ],
    tika='http://localhost:9998/',
    solr='http://localhost:8983/solr',
    fields=[
        Field('allowedRolesAndUsers',
              extractors=[ConstantExtractor(['Anonymous'])],
              multivalued=True),
        Field('effective',
              extractors=[IndexingTimeExtractor()],
              type_=datetime),
        Field('expires',
              extractors=[ConstantExtractor(datetime(2050, 12, 31))],
              type_=datetime),
        Field('getRemoteUrl',
              extractors=[URLExtractor()]),
        Field('SearchableText',
              extractors=[PlainTextExtractor()]),
        Field('Title',
              extractors=[TitleExtractor()]),
        Field('UID',
              extractors=[UIDExtractor()]),
    ]
)
