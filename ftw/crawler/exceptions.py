class FtwCrawlerException(Exception):
    """Base class for all our own exceptions.
    """


class FetchingError(FtwCrawlerException):
    """An error happend while attempting to fetch a resource.
    """


class ExtractionError(FtwCrawlerException):
    """An error happend while attempting to apply an extractor.
    """


class NoValueExtracted(ExtractionError):
    """The extractor was unable to extract a value.
    """


class SolrError(FtwCrawlerException):
    """Solr returned a non-200 response for an operation.
    """


class NoSuchField(FtwCrawlerException):
    """A field that doesn't exist was specified by name.
    """


class AttemptedRedirect(FtwCrawlerException):
    """An URL attempted a redirect to another location.
    """


class NotModified(FtwCrawlerException):
    """A resource hasn't been modified since the last time it got indexed.
    """


class ConfigError(FtwCrawlerException):
    """A configuration error occurred.
    """


class SiteNotFound(ConfigError):
    """The requested site could not be found in the configuration.
    """


class NoSitemapFound(FtwCrawlerException):
    """No sitemap could be found for the given site.
    """
