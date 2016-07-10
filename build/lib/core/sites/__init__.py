#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from core import database


class Site(object):
    def __init__(self, data=None, *args, **kwargs):
        self._supported_exts = []
        self._supports_subs = True
        self.headers = {'referer': 'https://github.com/Hellowlol/AutoUp'}
        self.uploadform = {}

    def login(self):
        pass

    def prepare(self):
        """ Prepare the files for THIS site """

    def upload(self, data):
        """ returns a dict with info """
        data = self.prepare(data)

    def _upload(self):
        """ real upload """
        pass

    def has_torrent(self, filename):
        pass

    def search(self, q):
        pass

