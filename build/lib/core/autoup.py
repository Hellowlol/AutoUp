#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import print_function
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import logging
import click

from sites import norbits
from config import make_default_config
from mediaelements import Video, Audio
from configobj import ConfigObj

import importlib
import glob

AUDIO_EXT = ()  #('.mp3', '.flac', '.ogg' '.aac')
VIDEO_EXT = ('.mkv', '.avi', '.mp4', '.wmv', '.flv')

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

log = logging.getLogger(__name__)


@click.command()
@click.option('--config', type=click.Path(exists=True))
@click.option('--upload', type=click.Path(exists=True))
@click.option('--report', default=False)
@click.option('--webserver', default=False)
@click.option('--scan', type=click.Path(exists=True))
@click.option('--loglevel', default='info')
@click.option('--enabled_sites', type=click.Choice(['all', 'norbits']))
@click.option('--default_config')
@click.option('--watched_paths', type=click.Path())
@click.option('--dry_run', default=False)
def cli(config, upload, report, webserver, scan, loglevel, enabled_sites, default_config, watched_paths, dry_run, *args, **kwargs):
    """ Main stuff for Autoup """
    if config is None:
        if not os.path.isfile(os.path.join(CURRENT_PATH, 'default_config.ini')):
            click.echo('There was no default config, creating one')
            config = make_default_config(os.path.join(CURRENT_PATH, 'default_config.ini'))
        else:
            config = os.path.join(CURRENT_PATH, 'config.ini')
            click.echo('Using %s ' % config)

    if default_config:
        config = make_default_config(default_config) or os.path.join(CURRENT_PATH, 'default_config.ini')
        config = os.path.abspath(config)

    if enabled_sites:
        enabled_sites = enabled_sites.split()

    if watched_paths:
        watched_paths = watched_paths.split()

    print locals()
    au = Autoup(config_file=config, enabled_sites=enabled_sites, watched_paths=watched_paths, loglevel=loglevel)

    if dry_run:
        print au._enabled_sites

    if scan:
        au.scan(scan)

    if webserver:
        # blocks forever
        au.webserver()

    return "lol"

class Fsh(FileSystemEventHandler):

    def on_created(self, event):
        print('on_created')
        return event.src_path


class Autoup(object):
    """ Class to Auto upload files to your favorite
        torrent tracker"""

    def __init__(self, config_file=None, watched_paths=None, enabled_sites=None, dry_run=False, *args, **kwargs):  # add kwargs

        self._config_file = config_file
        print ('config_file was', self._config_file)
        self.config = ConfigObj(self._config_file, encoding='utf-8')
        self._enabled_sites = self.load_sites(enabled_sites)
        self.__watch_paths = watched_paths or self.config['general']['watched_paths']
        self.__watcher = Observer()
        self.__torrent_sites = [norbits.Norbits()]

        self._use_torrent_site = kwargs.get('torrent_sites')
        self.dry_run = dry_run

    def _load_config(self, section):
        pass

    def sites(self, path=None):
        """ try to load all python in sites folder """
        pass

    def load_sites(self, enabled_sites):


        if enabled_sites is None:
            enabled_sites = self.config['general']['watched_paths']

        sites = []
        for name in glob.glob(os.path.join(CURRENT_PATH, 'sites/') + '*.py'):
            #filename = '%s.py' % name
            filename = os.path.splitext(os.path.basename(name))[0]
            print(filename)
            if not name.startswith('_') and filename in enabled_sites:
                m = importlib.import_module('core.sites.%s' % filename)

                #my_class = getattr(m, name.capitalize())
                #print(my_class)
                #sites.append(my_class())

        print(sites)
        return sites

    def upload(self, media_elements=None):
        """ Upload the torrent to the torrent sites """

        if media_elements is None:
            media_elements = self.scan()

        if not isinstance(media_elements, list):
            media_elements = list(media_elements)

        # Make media elements from paths
        media_elements = self.prepare(media_elements)

        for site in self.enabled_sites:  # Just add site param to?
            for media_element in media_elements:
                s = self._upload_site(site, media_element, self.dry_run)

    def upload_test(self, media_elements=None):
        """ Upload the torrent to the torrent sites """

        if media_elements is None:
            media_elements = self.scan()

        if not isinstance(media_elements, list):
            media_elements = list(media_elements)

        # Make media elements from paths
        media_elements = self.prepare(media_elements)
        forms = []
        for site in self.enabled_sites:  # Just add site param to?
            for media_element in media_elements:
                s = self._upload_site2(site, media_element)# is org
                forms.append(s)

        from pprint import pprint
        pprint(forms)

    def _upload_site2(self, site, media_element):
        # test
        return site.upload2(media_element)

    def _upload_site(self, site, media_element):
        return site.upload(media_element)

    def download(self, torrent, path=None):
        """ Download a torrent, intended to be used from cross posting """
        pass

    def seed(self):
        """ start add the torrent to your torrent client """
        pass

    def scan(self, paths=None):
        """ find the abs path of all the files in the watched paths """
        af = []

        if paths is None:
            paths = self.__watch_paths

        if isinstance(paths, str):
            paths = [paths]

        for fp in paths:
            if os.path.isfile(fp):
                af.append(fp)
                continue
            elif os.path.isdir(fp):
                af += [os.path.join(fp, i) for i in os.listdir(fp)]

        return af

    def prepare(self, files):
        """ Build media elements """

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


    def test_prepare(self):  # remove this
        tp = self.prepare(self.scan())
        print(tp)
        for ff in tp:
            pass
            #print(ff.extract())
        return tp

    def test_forms():
        pass

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

    def webserver(self):
        # add a simple cp server with stats?
        pass

    def stats(self, query):
        """ Query the db for uploa for x sites since y time """


if __name__ == '__main__':  # pragma: no cover
    pass
    #import time
    #start = time.time()
    #AU = Autoup()
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
