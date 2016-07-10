# mediaelements.py


import os

from guessit import guessit
from helpers import get_media_info
from torrentool.api import Torrent

#
#from mediafile import MediaFile


class BaseElement(object):
    def __init__(self, path, save_torrent_path=None, *args, **kwargs):
        self.type = self.__class__.__name__.lower()
        self.name, self.ext = os.path.splitext(path)
        self.fp = path
        self.save_folder = save_torrent_path
        self.torrent_name = None

    def to_torrent(self, save_path=None):
        if save_path is None:
            save_path = os.path.join(os.getcwd(), (self.name + '.torrent')) # Fix me!

        new_torrent = Torrent.create_from(self.fp) #
        #new_torrent.announce_urls = 'udp://tracker.openbittorrent.com:80'
        new_torrent.to_file(save_path) # fix me
        self.torrent_name = os.path.basename(save_path)
        return new_torrent, save_path

        """0-250MB:                     256KB (262144 bytes)
            250-1024MB:                  1MB   (1048576 bytes)
            1-5GB:                       2MB   (2097152 bytes)
            5-20GB:                      4MB   (4194304 bytes)
            20-40GB:                     8MB   (8388608 bytes)
            40 GB+:                      16MB  (16777216 bytes)
        """
        # Send a pr to make a better torrent
        # https://torrentfreak.com/how-to-make-the-best-torrents-081121/ fix

    def extract(self):
        """ Extract as much info about the elements as possible """
        pass

    def to_base64(self):
        """ Allow easy upload to torrent clients """
        pass # too


class Video(BaseElement):
    def __init__(self, path, save_torrent_path=None, *args, **kwargs):
        super(self.__class__, self).__init__(path, *args, **kwargs)
        self.type = 'video'
        self.fp = path
        self.info = {}
        self.files = []
        print("videoz")
        print(path)

        #self.extract()

        self.has_nfo = False
        self.has_images = []

        fps = []
        if os.path.isdir(path):
            fps = []
            for root, dirs, files in os.walk(path):
                for f in files:
                    fps.append(os.path.join(root, f))

            for ff in fps:
                print(ff)
                self.files.append(files)
                if ff.endswith('.nfo'):
                    self.has_nfo = ff
                elif ff.endswith(('.jpg', '.png')):
                    self.has_images.append(ff)

        else:
            self.files.append(path)

    def extract(self, path=None, rb=None):

        if path is None:
            path = self.fp

        info = guessit(path)
        self.info.update(info)
        self.info['filepath'] = path

        media_info = get_media_info(path)
        if media_info:
            self.info['media_info'] = media_info

        return self.info


class Audio(BaseElement):
    def __init__(self, path, *args, **kwargs):
        super(self.__class__, self).__init__(path, *args, **kwargs)
        pass # todo

    def extract(self, path=None):
        # use https://github.com/beetbox/mediafile/when updated
        pass
