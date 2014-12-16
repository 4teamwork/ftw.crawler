from ftw.crawler.utils import mkdir_p
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
from logging import StreamHandler
import logging
import os
import sys


LOGDIR = 'var/log/'
CONSOLE_FORMAT = '%(levelname)-8s %(module)-10s %(message)s'
FILE_FORMAT = '%(asctime)s %(levelname)-8s %(module)-10s %(message)s'
file_formatter = Formatter(FILE_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')


def create_log_dir():
    script_path = os.path.abspath(sys.argv[0])
    bin_dir = os.path.dirname(script_path)
    if bin_dir.endswith('bin'):
        # Use the /bin directory's parent as base
        base_dir = os.path.split(bin_dir)[0]
    else:
        # Unless there is no /bin - default to cwd
        base_dir = os.getcwd()

    # Create log directory relative to base
    log_dir = os.path.join(base_dir, LOGDIR)
    mkdir_p(log_dir)
    return log_dir


def setup_logging():
    log_dir = create_log_dir()
    logging.root.setLevel(logging.DEBUG)

    # StreamHandler logging to console (stderr) at level INFO
    console_handler = StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(Formatter(CONSOLE_FORMAT))
    logging.root.addHandler(console_handler)

    # FileHandler logging to 'debug.log' at level DEBUG
    debug_file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'debug.log'), when='midnight', backupCount=30)
    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(file_formatter)
    logging.root.addHandler(debug_file_handler)

    # FileHandler logging to 'info.log' at level INFO
    info_file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'info.log'), when='midnight', backupCount=30)
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(file_formatter)
    logging.root.addHandler(info_file_handler)

    # FileHandler logging to 'warn.log' at level WARN
    warn_file_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'warn.log'), when='midnight', backupCount=30)
    warn_file_handler.setLevel(logging.WARN)
    warn_file_handler.setFormatter(file_formatter)
    logging.root.addHandler(warn_file_handler)

    # Only log messages from the requests library with at least level WARN
    requests_logger = logging.getLogger('requests')
    requests_logger.setLevel(logging.WARN)
