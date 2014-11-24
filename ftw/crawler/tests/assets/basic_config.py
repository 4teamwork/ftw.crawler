from ftw.crawler.configuration import Config
from ftw.crawler.configuration import Field
from ftw.crawler.configuration import Site
from ftw.crawler.extractors import TitleExtractor


CONFIG = Config(
    sites=[
        Site('http://www.sitemapxml.co.uk/'),
        Site('https://www.dropbox.com/'),
    ],
    tika='http://localhost:9998/',
    solr='http://localhost:8983/solr',
    fields=[
        Field('Title',
              extractors=[TitleExtractor()],
              type_=str),
    ]
)
