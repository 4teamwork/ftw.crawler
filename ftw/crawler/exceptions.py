class FtwCrawlerException(Exception):
    """Base class for all our own exceptions.
    """


class FetchingError(FtwCrawlerException):
    """An error happend while attempting to fetch a resource.
    """
