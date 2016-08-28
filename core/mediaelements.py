# mediaelements.py


import os
import logging

from guessit import guessit
from helpers import get_media_info, make_images_from_video
from torrentool.api import Torrent
from core import VIDEO_EXT, TORRENTS_PATH, CONFIG


#
#from mediafile import MediaFile

log = logging.getLogger(__name__)


class BaseElement(object):
    def __init__(self, path, scan_path, save_torrent_path=None, *args, **kwargs):
        self.type = self.__class__.__name__.lower()
        self.name, self.ext = os.path.splitext(path)
        self.fp = path
        self.scan_path = scan_path
        self.save_folder = save_torrent_path
        self.torrent_name = None
        self.save_torrent_path = save_torrent_path

        if self.save_torrent_path is None:
            self.save_torrent_path = TORRENTS_PATH

    def to_torrent(self, save_path=None, announce_urls=None):
        """Create a torrent

           Args:
                save_path (str, None): save torrent to this location if omitted
                                       its saved to the userdata/torrents foler
                announce_urls (str, list): list of trackers

        """
        if save_path is None:
            save_path = os.path.join(self.save_torrent_path, os.path.basename(self.name) + '.torrent')

        self.torrent_name = os.path.basename(save_path)
        new_torrent = Torrent.create_from(self.fp)

        if announce_urls:
            new_torrent.announce_urls = announce_urls

        new_torrent.to_file(save_path)

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
    def __init__(self, path, scan_path=None, save_torrent_path=None, *args, **kwargs):
        super(self.__class__, self).__init__(path, scan_path, *args, **kwargs)
        self.type = 'video'
        self.fp = path
        self.scan_path = scan_path
        self.info = {}
        self.files = []
        self.has_nfo = False
        self.has_images = []
        self.autoup_added_images = False
        self.summary = ''

        fps = []
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    fps.append(os.path.join(root, f))

            for ff in fps:
                self.files.append(ff)
                if ff.endswith('.nfo'):
                    self.has_nfo = ff
                elif ff.endswith(('.jpg', '.png')):
                    self.has_images.append(ff)

        else:
            self.files.append(path)

    def extract(self, path=None, rb=None):
        vfile = None

        if path is None:
            path = self.fp

        z = [i for i in self.files if i.endswith(VIDEO_EXT) and 'sample' not in i]

        if len(z) == 1:
            vfile = z[0]
            info = guessit(vfile)
        else:
            info = guessit(path)

        if CONFIG['general'].get('video_summary', True): # fix true
            if info.get('type') == 'episode':
                log.debug('Should be a fucking episode')
                log.debug('self.files = %s' ''.join(self.files))
            elif info.get('type') == 'movie':
                pass

        self.info.update(info)
        # orginal path
        self.info['filepath'] = path

        # Extact some images from video files
        if not self.has_images:
            self.autoup_added_images = True
            log.debug('This file has no images, gonna try to extract some')
            img = [make_images_from_video(k) for k in z]
            for zz in img:
                self.has_images.extend(zz)

        media_info = get_media_info(vfile or path)
        if media_info:
            self.info['media_info'] = media_info

        return self.info


class Audio(BaseElement):
    def __init__(self, path, *args, **kwargs):
        super(self.__class__, self).__init__(path, *args, **kwargs)
        pass  # todo

    def extract(self, path=None):
        # use https://github.com/beetbox/mediafile/when updated
        pass
