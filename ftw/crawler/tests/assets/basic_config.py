from ftw.crawler.configuration import Config
from ftw.crawler.configuration import Site


CONFIG = Config(
    sites=[
        Site('http://www.sitemapxml.co.uk/'),
        Site('https://www.dropbox.com/'),
    ],
)
