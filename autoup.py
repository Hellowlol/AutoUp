#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import print_function
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading


AUDIO_EXT = ['.mp3']
VIDEO_EXT = ['mkv', 'avi', 'mp4']

class Fsh(FileSystemEventHandler):

    def on_created(self, event):
        print(event)
        print('on_created')
        print(event.src_path)
        return event.src_path



class Autoup(object):
    """ Class to Auto upload files to your favorite
        torrent tracker"""

    def __init__(self, *args, **kwargs):  # add kwargs
        self.enabled_sites = []
        #self.__watch_paths = []
        self.__watch_paths = ['C:\\htpc\\test_watch_dog']
        self.__watcher = Observer()
        self.__torrent_sites = []

    def sites(self):
        pass

    def upload(self, media_elements=None):
        """ Upload the torrent to the torrent sites """

        if media_elements is None:
            media_elements = self.scan()

        if not isinstance(media_elements, list):
            media_elements = list(media_elements)

        for site in self.enabled_sites: # Just add site param to?
            for fp in media_elements:
                s = self._upload_site(site, fp)
                s.upload()

    def _upload_site(self, site, fp):
        s = site(fp).prepare()
        s.upload()

    def download(self, torrent, path=None):
        """ """
        pass

    def seed(self):
        """ start add the torrent to your torrent client """
        pass

    def scan(self, paths=None):
        """ find the abs path of all the files in the watched paths """
        af = []

        if paths is None:
            paths = self.__watch_paths

        if isinstance(paths, basestring):
            paths = [paths]

        for fp in paths:
            abs_fp = os.path.abspath(fp)
            for directory, dirnames, filenames in os.walk(abs_fp):
                for f in filenames:
                    af.append(os.path.join(directory, f))

        return af

    def prepare(self, files):
        prep_files = []
        for f in files:
            name, ext = os.path.splitext(f)
            if ext in VIDEO_EXT:
                prep_files.append(Video(f))
            elif ext in AUDIO_EXT:
                prep_files.append(Audio(f))

        return prep_files

    def add_watch_path(self, path):
        self.__watch_paths.append(path)

    def _watch(self):
        event_handler = Fsh()
        for fp in self.__watch_paths:
            self.__watcher.schedule(event_handler, fp, recursive=True)

        self.__watcher.start()

        try:
            while True:
                time.sleep(1)
                print('***')
        except KeyboardInterrupt:
            self.__watcher.stop()

        self.__watcher.join()

    def __watch(self):
        thread = threading.Thread(target=self._watch)
        thread.daemon = True
        thread.start()
        thread.join()

    def watch(self):
        self.__watch()

    def test(self):
        print('This is a lame test')


class BaseElement(object):
    def __init__(self, path, *args, **kwargs):
        self.type = self.__class__.name.lower()
        self.name, self.ext = os.path.splitext(path)

    def pop(self):
        pass

    def extract(self):
        pass


class Video(BaseElement):
    def __init__(self, path, *args, **kwargs):
        super(self.__class__, self).__init__(path, *args, **kwargs)
        self.type = 'video'
        self.fp = path
        self.info = {}

    def extract(self):
        from guessit import guessit
        import enzyme
        info = guessit(self.fp)
        self.info.update(info)
        self.info['filepath'] = self.fp

        if self.ext == '.mkv':
            with open(self.fp) as f:
                mkv = enzyme.MKV(f)

        return self.info

class Audio(BaseElement):
    def __init__(self, path, *args, **kwargs):
        super(self.__class__, self).__init__(path, *args, **kwargs)


if __name__ == '__main__':  # pragma: no cover
    AU = Autoup()
    AU.scan()
    #AU.watch()
    #AU.test()
    # add cli option so its ez to cross post
