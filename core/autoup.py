#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import logging
import click



import importlib
import glob
import os
import six
import core
from core import CURRENT_PATH, USERDATA_PATH, VIDEO_EXT, AUDIO_EXT, initialize
 # has to be imported after initalize
from core import CONFIG

print'top autoup', CONFIG

log = logging.getLogger(__name__)

class Fsh(FileSystemEventHandler):

    def on_created(self, event):
        print('on_created')
        return event.src_path


class Autoup(object):
    """ Class to Auto upload files to your favorite
        torrent tracker"""

    def __init__(self, config_file=None, watched_paths=None,
                 enabled_sites=None, enabled_clients=None, dry_run=False, report=False,
                 comment=False, *args, **kwargs):  # add kwargs

        self._config_file = config_file
        # Init_config file
        initialize(self._config_file)
        # Oh, i feels to dirty # fixme
        from core import CONFIG
        self.config = CONFIG
        #core.CONFIG = CONFIG
        self.comment = comment
        self._enabled_sites = self.load_sites(enabled_sites)
        self_enabled_clients = self.load_clients(enabled_clients)
        self.__watch_paths = watched_paths or self.config.WATCHED_PATHS
        self.__watcher = Observer()
        self.dry_run = dry_run
        self._resport = report

    def _load_config(self, section):
        pass

    def sites(self, path=None):
        """ try to load all python in sites folder """
        pass

    def load_clients(self, enabled_clients=None):
        """Simple function that dynamically loads the torrent sites

            Args:
                enabled_clients (str, list, none): loads from config file if omitted

            Returns:
                A list of clients initalized
        """

        if enabled_clients is None:
            enabled_clients = '' # fix me

        from core.clients import qbt
        print self.config.get('qbittorrent')
        #enabled_clients = [qbt.Qbittorrent(self.config.get('qbittorrent'))]

    def load_sites(self, enabled_sites=None):
        """Simple function that dynamically loads the torrent sites

            Args:
                enabled_sites (str, list, none): loads from config file if omitted

            Returns:
                A list of torrent sites initalized
        """

        if enabled_sites is None:
            enabled_sites = self.config.ENABLED_SITES

        # If it was passed manually as a cmd line arg
        if isinstance(enabled_sites, (six.binary_type, six.text_type)):
            enabled_sites = enabled_sites.split()

        sites = []

        if not len(enabled_sites):
            log.warning('There isnt any enabled torrent sites')

        for name in glob.glob(os.path.join(CURRENT_PATH, 'sites/') + '*.py'):
            basename = os.path.splitext(os.path.basename(name))[0]
            if not name.startswith('_') and basename in enabled_sites:
                for k, v in self.config.items():
                    if k == basename:
                        m = importlib.import_module('core.sites.%s' % basename)
                        my_class = getattr(m, basename.capitalize())
                        c_dict = self.config[k].copy()
                        c_dict['comment'] = self.comment
                        sites.append(my_class(**c_dict))

        return sites

    def upload(self, media_elements=None, seed=None):
        """Upload the torrent to the torrent sites

           Args:
                media_elements (class.mediaelements): If media_elements is omitted
                this function will scan the default paths for media_elements

            Returns:

        """

        if seed is None:
            seed = True # core.CONFIG.SEED # fix me

        if media_elements is None:
            # default paths
            media_elements = self.scan()
        else:
            media_elements = self.scan(media_elements)

        if not isinstance(media_elements, list):
            media_elements = list(media_elements)

        # Make media elements from paths
        media_elements = self.prepare(media_elements)
        torrent_files = []

        for site in self._enabled_sites:  # Just add site param to?
            for media_element in media_elements:
                s, tf = self._upload_site(site, media_element, self.dry_run)
                torrent_files.append(tf)

        if seed is True:
            self.seed(torrent_files)

    def _upload_site(self, site, media_element, dry_run):

        return site.upload(media_element, dry_run=dry_run)

    def download(self, torrent, path=None):
        """ Download a torrent, intended to be used from cross posting """
        pass

    def seed(self):
        """ start add the torrent to your torrent client """


    def scan(self, paths=None):
        """ find the abs path of all the files in the watched paths """
        af = []

        if paths is None:
            paths = self.__watch_paths

        if isinstance(paths, (six.binary_type, six.text_type)):
            paths = [paths]

        for fp in paths:
            if os.path.isfile(fp):
                af.append(fp)
                continue
            elif os.path.isdir(fp):
                af += [os.path.join(fp, i) for i in os.listdir(fp)]

        return af

    def prepare(self, files):
        """Build media elements

           Args:
                files (list): List of filepaths

            Returns:
                list of media_elements

        """
        from mediaelements import Video, Audio # fix me, has to be import after the config is initialized

        def do_files(f):
            if os.path.isfile(f):
                name, ext = os.path.splitext(os.path.basename(f))
                if ext.lower() in VIDEO_EXT:
                    return Video(f)
                elif ext.lower() in AUDIO_EXT:
                    return Audio(f)

            if os.path.isdir(f):
                for root, dirs, files in os.walk(f):
                    for _f in files:
                        name, ext = os.path.splitext(os.path.basename(_f))
                        if ext.lower() in VIDEO_EXT:
                            return Video(f)
                            break
                        elif ext.lower() in AUDIO_EXT:
                            return Audio(f)
                            break

        return filter(None, list(do_files(f) for f in files))

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
        #thread.join()

    def watch(self):
        self._watch()

    def test(self):
        log.debug('This is a lame test')

    def webserver(self, z=None):
        # add a simple cp server with stats?
        log.debug('I should have started a webserver %s' % z)
        from core.web import start
        start()

    def stats(self, query):
        """ Query the db for upload for x sites since y time """
        pass

    def table(self):
        """ xxx """
        pass



if __name__ == '__main__':  # pragma: no cover
    pass
    #import time
    #start = time.time()
    AU = Autoup()
    AU.load_clients()
    #AU.scan()
    #AU.sites()
    #AU.upload()
    #t = time.time() - start
    #print('total time was %s' % (t))

    #AU.upload_test()
    #AU.test_prepare()
    #AU.watch()
    #AU.test()
    # add cli option so its ez to cross post
