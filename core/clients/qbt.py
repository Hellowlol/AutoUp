import Client

# pip install python-qbittorrent
#from qbittorrent import Client as q_client

class Qbittorrent(Client):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(data, *args, **kwargs)
