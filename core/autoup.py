#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import importlib
import logging
import os
import threading
import time

import click
import six
from tqdm import tqdm
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


from core import CURRENT_PATH, VIDEO_EXT, AUDIO_EXT, initialize
import core


log = logging.getLogger(__name__)


class Fsh(FileSystemEventHandler):

    def __init__(self, au):
        self.au = au

    def on_created(self, event):
        print('on_created')
        self.au.upload(event.src_path)
        return event.src_path


class Autoup(object):
    """ Class to Auto upload files to your favorite
        torrent tracker"""

    def __init__(self, config=None, watched_paths=None,
                 enabled_sites=None, enabled_clients=None, dry_run=False, report=False,
                 comment=False, *args, **kwargs):  # add kwargs

        if isinstance(config, str):
            core.CONFIG = config = initialize(config)

        self._config_file = core.CONFIG._config_file
        self.config = core.CONFIG
        self.comment = comment
        self._enabled_sites = self.load_sites(enabled_sites)
        self._enabled_clients = self.load_clients(enabled_clients)
        self.__watch_paths = watched_paths or self.config.WATCHED_PATHS
        self.__watcher = Observer(timeout=10)
        self.dry_run = dry_run
        self._resport = report

    def load_clients(self, enabled_clients=None):
        """Simple function that dynamically loads the torrent sites

            Args:
                enabled_clients (str, list, none): loads from config file if omitted

            Returns:
                A list of clients initalized
        """

        if enabled_clients is None:
            enabled_clients = self.config.ENABLED_CLIENTS

        # If it was passed manually as a cmd line arg
        if isinstance(enabled_clients, (six.binary_type, six.text_type)):
            enabled_clients = enabled_clients.split()

        if not len(enabled_clients):
            log.warning('There isnt any enabled torrent clients')

        clients = []

        for name in glob.glob(os.path.join(CURRENT_PATH, 'clients/') + '*.py'):
            basename = os.path.splitext(os.path.basename(name))[0]
            real_basename = basename
            if real_basename == 'qbt':
                real_basename = 'qbittorrent'

            if not name.startswith('_') and real_basename in enabled_clients:
                for k, v in self.config.items():
                    if k in real_basename:
                        m = importlib.import_module(
                            'core.clients.%s' % basename)
                        my_class = getattr(m, real_basename.capitalize())
                        c_dict = self.config[k].copy()
                        if len(c_dict):
                            clients.append(my_class(**c_dict))

        return clients

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

    def upload(self, path=None, seed=True):
        """Upload the torrent to the torrent sites

           Args:
                path(string): filepath that the self.scan should use to create find files.
                seed(bool)

            Returns:

        """
        media_elements = self.scan(path)

        if not isinstance(media_elements, list):
            media_elements = list(media_elements)

        # Make media elements from paths
        media_elements = self.prepare(media_elements, path)
        torrent_files = []

        for site in tqdm(self._enabled_sites, desc='Sites:'):  # Just add site param to?
            for media_element in tqdm(media_elements, desc='torrents:'):
                s, tf, scan_path = self._upload_site(site, media_element, self.dry_run)
                if tf:
                    torrent_files.append((tf, scan_path))

        if seed is True:
            self.seed(torrent_files)

    def _upload_site(self, site, media_element, dry_run):
        return site.upload(media_element, dry_run=dry_run)

    def download(self, torrent, path=None):
        """ Download a torrent, intended to be used from cross posting """
        pass

    def seed(self, torrents=None, save_path=None, label=None):
        """ Add torrents the torrent clients and creates a progress bars

            Args:
                torrents(list): A list of tuples with the path to the torrent path and the scan path
                save_path(None): Dunno what the fuck this is fore fix plx

            Returns:
                None

        """

        click.echo('Adding torrents to the torrent clients')

        for client in tqdm(self._enabled_clients, desc='Torrent clients'):
            for t in tqdm(torrents, desc='torrents'):
                try:
                    client.download_torrent(*t)
                except Exception as e:
                    log.exception(e)

        print('\n')

    def scan(self, paths=None):
        """ find the abs path of all the files in the watched paths

            Args:
                paths(str, list): path to check if its a file or folder

            Returns:
                    list of file/files
        """
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

    def prepare(self, files, scan_path=None):
        """Build media elements

           Args:
                files (list): List of filepaths
                scan_path: This is used to set the correct seed location in self.seed

            Returns:
                list of media_elements

        """
        from mediaelements import Video, Audio

        def do_files(f):
            if os.path.isfile(f):
                name, ext = os.path.splitext(os.path.basename(f))
                if ext.lower() in VIDEO_EXT:
                    return Video(f, scan_path)
                elif ext.lower() in AUDIO_EXT:
                    return Audio(f, scan_path)

            if os.path.isdir(f):
                for root, dirs, files in os.walk(f):
                    for _f in files:
                        name, ext = os.path.splitext(os.path.basename(_f))
                        if ext.lower() in VIDEO_EXT:
                            return Video(f, scan_path)
                            break
                        elif ext.lower() in AUDIO_EXT:
                            return Audio(f, scan_path)
                            break

        return filter(None, list(do_files(f) for f in files))

    def add_watch_path(self, path):
        self.__watch_paths.append(path)

    def _watch(self, path=None):
        """ Watch files paths for changes. FHS  calls scan on the
            path that changed thus extracing metadata upload to
            the torrent sites seeding to torrent clients

            Args:
                path(string): File path to watch for changes

            Return:
                None

        """

        event_handler = Fsh(self)
        if path:
            self.__watch_paths.append(path)

        for fp in self.__watch_paths:
            self.__watcher.schedule(event_handler, fp, recursive=True)

        self.__watcher.start()

        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.__watcher.stop()

        self.__watcher.join()

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
