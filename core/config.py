import logging
import re
from configobj import ConfigObj
import os

"""
_CONFIG_DEFINITIONS = {
    'general': {
        'loglvl': 'info',
        'watched_paths': '',  #list
        'blocked': '',
        'media_info_cli': 'mediainfo',
        'episode_summary': '',
        'movie_summary': '',
        'enabled_sites': ''
    },
    'norbits': {
        'username': '',
        'password': '',
        'apikey': '',
        'valid_ext': []
    },
    'clients': {'qbittorrent': {'url': '',
                                'username': '',
                                'password': '',
                               },
                'deluge': {'url': '',
                           'username': '',
                           'password': ''}
    }
}
"""

log = logging.getLogger(__name__)


def bool_int(value):
    """
    Casts a config value into a 0 or 1
    """
    if isinstance(value, basestring):
        if value.lower() in ('', '0', 'false', 'f', 'no', 'n', 'off'):
            value = 0
    return int(bool(value))

_CONFIG_DEFINITIONS = {
    'LOGLVL': (str, 'general', 'info'),
    'WATCHED_PATHS': (list, 'general', ''),  #list
    'BLOCKED': (str, 'general', ''),
    'MEDIA_INFO_CLI': (str, 'general', 'media_info_cli'), # fullpath or in env path
    'EPISODE_SUMMARY': (bool, 'general', False),
    'MOVIE_SITES': (bool, 'general', False),
    'ENABLED_SITES': (list, 'general', ''),
    'FFMPEG': (str, 'general', 'ffmpeg'),
    'DB': (str, 'general', 'C:\Users\steffen\Documents\GitHub\AutoUp\userdata\autoup.db'), # fix me

    'IMGUR_CLIENT_ID': (str, 'imgur', '47d69f063752039'), # Use your own.
    'IMGUR_CLIENT_SECRET': (str, 'imgur', '34b43ca44eb088ed05f0ae1bbf22edcd489589a0'),

    'THETVDB_APIKEY': (str, 'thetvdb', 'C614040AE87171D0'),
    'THETVDB_USERNAME': (str, 'thetvdb', 'autoup'),
    'THETVDB_USERPASS': (str, 'thetvdb', 'A80D10B8022EBDFE'),



    # Norbits
    'NORBITS_USERNAME': (str, 'norbits', ''),
    'NORBITS_PASSWORD': (str, 'norbits', ''),
    'NORBITS_APIKEY': (str, 'norbits', ''),

    # Deluge
    'DELUGE_URL': (str, 'deluge', ''),
    'DELUGE_USERNAME': (str, 'deluge', 'deluge'),
    'DELUGE_PASSWORD': (str, 'deluge', 'deluge'),

    # Qbittorrent
    'QBITTORRENT_URL': (str, 'qbittorrent', ''),
    'QBITTORRENT_USERNAME': (str, 'qbittorrent', ''),
    'QBITTORRENT_PASSWORD': (str, 'qbittorrent', '')
}


class Config(object):
    """ Wraps access to particular values in a config file """

    def __init__(self, config_file):
        """ Initialize the config with values from a file """
        self._config_file = config_file
        self._config = ConfigObj(self._config_file, encoding='utf-8')
        for key in _CONFIG_DEFINITIONS.keys():
            self.check_setting(key)


    def _define(self, name):
        key = name.upper()
        ini_key = name.lower()
        definition = _CONFIG_DEFINITIONS[key]

        if len(definition) == 3:
            definition_type, section, default = definition
        else:
            definition_type, section, _, default = definition
        return key, definition_type, section, ini_key, default

    def check_section(self, section):
        """ Check if INI section exists, if not create it """
        if section not in self._config:
            self._config[section] = {}
            return True
        else:
            return False

    def check_setting(self, key):
        """ Cast any value in the config to the right type or use the default """
        key, definition_type, section, ini_key, default = self._define(key)
        self.check_section(section)
        try:
            my_val = definition_type(self._config[section][ini_key])
        except Exception:
            my_val = definition_type(default)
            self._config[section][ini_key] = my_val
        return my_val

    def write(self):
        """ Make a copy of the stored config and write it to the configured file """
        new_config = ConfigObj(encoding="UTF-8")
        new_config.filename = self._config_file

        # first copy over everything from the old config, even if it is not
        # correctly defined to keep from losing data
        for key, subkeys in self._config.items():
            if key not in new_config:
                new_config[key] = {}
            for subkey, value in subkeys.items():
                new_config[key][subkey] = value

        # next make sure that everything we expect to have defined is so
        for key in _CONFIG_DEFINITIONS.keys():
            key, definition_type, section, ini_key, default = self._define(key)
            self.check_setting(key)
            if section not in new_config:
                new_config[section] = {}
            new_config[section][ini_key] = self._config[section][ini_key]

        # Write it to file
        log.info("Writing configuration to file")

        try:
            new_config.write()
        except IOError as e:
            log.error("Error writing configuration file: %s", e)

    def __getattr__(self, name):
        """
        Returns something from the ini unless it is a real property
        of the configuration object or is not all caps.
        """
        if not re.match(r'[A-Z_]+$', name):
            return super(Config, self).__getattr__(name)
        else:
            return self.check_setting(name)

    def __getitem__(self, name):
        try:
            return self._config[name]
        except KeyError:
            key, definition_type, section, ini_key, default = self._define(name)
            self._config[section][ini_key] = definition_type(name)
            return self._config[section][ini_key]

    def __setattr__(self, name, value):
        """
        Maps all-caps properties to ini values unless they exist on the
        configuration object.
        """
        if not re.match(r'[A-Z_]+$', name):
            super(Config, self).__setattr__(name, value)
            return value
        else:
            key, definition_type, section, ini_key, default = self._define(name)
            self._config[section][ini_key] = definition_type(value)
            return self._config[section][ini_key]

    def process_kwargs(self, kwargs):
        """
        Given a big bunch of key value pairs, apply them to the ini.
        """
        for name, value in kwargs.items():
            key, definition_type, section, ini_key, default = self._define(name)
            self._config[section][ini_key] = definition_type(value)

    # proxy some funcs from configobj
    def reload(self):
        return self._config.reload()

    def clear(self):
        """ clears """
        return self._config.reset()

    # add dict like stuff
    def get(self, name, default=None):
        try:
            return self._config[name]
        except KeyError:
            return default

    def items(self):
        return self._config.items()

    def keys(self):
        return self._config.keys()

    def values(self):
        return self._config.values()
