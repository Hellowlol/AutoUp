from configobj import ConfigObj


_CONFIG_DEFINITIONS = {
    'general': {
        'loglvl': 'info',
        'watched_paths': '',  #list
    },
    'norbits': {
        'username': '',
        'password': '',
        'apikey': ''
    }
}


def make_default_config(filepath):
    c = ConfigObj(_CONFIG_DEFINITIONS)
    c.filename = filepath
    c.write()

    return filepath
