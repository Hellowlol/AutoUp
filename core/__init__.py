import logging
import logging.handlers


import os
import sys
import threading
import core.config
import requests

#from configobj import ConfigObj

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    # 2.6
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

RUN_DIR = os.path.dirname(__file__)

VIDEO_EXT = ('.mkv', '.avi', '.mp4', '.wmv', '.flv')
AUDIO_EXT = ()  #('.mp3', '.flac', '.ogg' '.aac')

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
USERDATA_PATH = os.path.join(os.path.dirname(CURRENT_PATH), 'userdata')
TORRENTS_PATH = os.path.join(USERDATA_PATH, 'torrents')
CONFIG = None
INIT_LOCK = threading.Lock()

logging.getLogger(__name__).addHandler(NullHandler())

# Create missing folders..
try:
    os.makedirs(USERDATA_PATH)
except OSError as e:
    if not os.path.isdir(USERDATA_PATH):
        raise

try:
    os.makedirs(TORRENTS_PATH)
except OSError as e:
    if not os.path.isdir(TORRENTS_PATH):
        raise


def initialize(config_file=None, lvl=None):
    """ Initialize the config and logging

        Args:
            config_file(str): ''
            lvl(bool): ''

        Returns:
                config object

    """
    with INIT_LOCK:
        global CONFIG

        # Use default config path
        if config_file is None:
            config_file = os.path.join(USERDATA_PATH, 'config.ini')

        CONFIG = core.config.Config(config_file)

        if not os.path.exists(config_file):
            CONFIG.write()

        log_path = os.path.join(USERDATA_PATH, 'log.txt')

        handlers = []

        log = logging.getLogger(__name__)

        # Check the config file if cmd line isnt parsed
        if lvl is None and CONFIG.LOGLVL == 'debug':
            lvl = True

        if lvl:
            SH = logging.StreamHandler(sys.stdout)
            handlers.append(SH)

        if log_path:
            FH = logging.handlers.RotatingFileHandler(log_path, maxBytes=25000000, backupCount=2)
            handlers.append(FH)

        logformatter = logging.Formatter('%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s', "%Y-%m-%d %H:%M:%S")

        if lvl:
            loglevel = logging.DEBUG
        else:
            loglevel = logging.INFO

        # Disable cherrypy access log
        logging.getLogger('cherrypy.access').propagate = False

        for h in handlers:

            if h:
                h.setLevel(loglevel)
                h.setFormatter(logformatter)
                #log.addHandler(h)
                logging.getLogger('').addHandler(h)

        log.setLevel(loglevel)

        # Silence some loggers
        for q in ['requests', 'urllib3', 'rebulk', 'cachecontrol', 'tvdbapi_client']:
            try:
                logging.getLogger(q).setLevel(logging.WARNING)
            except:
                pass

        return CONFIG


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

#sys.excepthook = handle_exception