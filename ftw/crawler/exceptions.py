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
