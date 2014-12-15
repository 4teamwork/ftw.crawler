import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)-8s %(module)-10s %(message)s')

    # Only log messages from the requests library with at least level WARN
    requests_logger = logging.getLogger('requests')
    requests_logger.setLevel(logging.WARN)
