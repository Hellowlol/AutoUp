
import logging
import records

log = logging.getLogger(__name__)

def Database(object):
    def __init__(self, fp):
        self.fp = fp
        self.records = records.Database('sqlite:///%s' % fp)

    def create_table(self):
        self.records.query('CREATE TABLE persons (key int PRIMARY KEY, fname text, lname text, email text)')


    #
    'torrent_raw, torrent_name, size, torrent_hash, comment. time, upload_form'





