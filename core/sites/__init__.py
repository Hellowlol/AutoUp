#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import db

class Site(object):
    def __init__(self, data=None, *args, **kwargs):
        self.__class__.lower().url = ''
        self.__class__.lower().apikey = ''
        self._supported_exts = []
        self._supports_subs = True


    def prepare(self):
        """ Prepare the files for THIS site """



    def upload(self, data):
        """ data """
        pass
