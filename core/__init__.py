import logging
import os
import sys
import threading
import requests
import rebulk
import core.config
import cachecontrol
import tvdbapi_client

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


def initialize(config_file):
    #print "was initialize"

    with INIT_LOCK:
        global CONFIG

        # Use default config path
        if config_file is None:
            config_file = os.path.join(USERDATA_PATH, 'config.ini')

        CONFIG = core.config.Config(config_file)
        #print('CONFIG inside initialize %s' % CONFIG)

        if not os.path.exists(config_file):
            CONFIG.write()

        logging.getLogger(__name__).addHandler(NullHandler())

        logging.basicConfig(stream=sys.stdout, level=20)

        # Silence some loggers
        to_silence = ['requests', 'urllib3', 'rebulk', 'cachecontrol', 'tvdbapi_client']

        for q in to_silence:
            logging.getLogger(q).setLevel(logging.WARNING)


