#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import Site

import json
import os
import sys

import requests
from bs4 import BeautifulSoup as bs
import re
import logging
from core.sites import Site
#import sites
from core.helpers import imdb_aka, load_secret_file

from pprint import pprint as pp

log = logging.getLogger(__name__)

#def load_secret_file(key, path='C:\\htpc\\password_list.json'):
#    with open(path, 'r') as p:
#        r = json.load(p)
#        if key in r:
#            return r.get(key)


class Norbits(Site):
    """ Handles all the Norbits shit """

    categories = {}

    def __init__(self, data=None, *args, **kwargs):
        super(self.__class__, self).__init__(data, *args, **kwargs)
        self.norbits_url = 'http://www.norbits.net/upload.php'
        self.norbits_login_url = 'http://www.norbits.net/takelogin.php'
        self.norbits_upload_url = 'http://www.norbits.net/takeupload.php'
        self.norbits_cat_url = 'http://www.norbits.net/browse.php'
        self.norbits_apikey = ''
        self.session = requests.Session()
        self.login_attempts = 0
        self.site_disabled = False

        #print(self._build_categories())

        # Add a real config
        self.username = load_secret_file('norbits_username') or kwargs.get('norbits_username')
        self.password = load_secret_file('norbits_password') or kwargs.get('norbits_password')
        self.apikey = load_secret_file('norbits_apikey') or kwargs.get('norbits_apikey')

        # Keep
        self.uploadform = {'MAX_FILE_SIZE': '3145728',
                           'file': (None, ''),
                           'name': (None, 'name'),
                           'nfo': (None, '', 'application/octet-stream'), # Drop nfo atm
                           'nfopos': (None, 'top'),
                           'infourl': (None, ''),
                           'descr': (None, ''),
                           'main': (None, ''),
                           'sub_1': (None, ''),
                           'sub_2': (None, ''),
                           'sub_3': (None, ''),
                           'mediainfo': (None, '')
                           }

    def login(self, to='/upload.php'):
        data = {'username': self.username, # fix me
                'password': self.password,
                'returnto': to}

        r = self.session.post(self.norbits_login_url, headers=self.headers, data=data)
        log.debug('Tried to login to Norbits', r.status_code)
        print('Tried to login to Norbits', r.status_code)
        return r.status_code

    def fetcher(self, path, action='get', data=None, files=None):
        r = None

        if action == 'get':
            r = self.session.get(path)
        elif action == 'post' and files:
            r = self.session.post(path, files=files)
        elif action == 'post' and data:
            r = self.session.post(path, data=data)

        if self.login_attempts > 3:
            self.site_disabled = True

        log.debug('url=%s action=%s status=%s' % (r.url, action, r.status_code))
        log.debug(r.text.encode('utf-8'))


        # We are not logged in and is taken to the login site
        if (r.status_code == 302 and r.url == 'http://www.norbits.net/takelogin.php' or
            r.status_code == 200 and '/login.php?' in r.url):
            if not self.site_disabled or self.login_attempts > 3:
                self.login_attempts += 1
                if self.login() == 200:
                    log.debug('Successfull login to norbits')
                    # Do the same call again
                    return self.fetcher(path, action=action, data=data)

        return r

    def upload(self, data, dry_run):
        """ Takes a dict or media_element"""
        # Check if the torrent already exist on the tracker
        #self.search(data) # fix me

        # Check that we hasnt uploaded that url before, check db

        # _.upload expects a dict
        if not isinstance(data, dict):
            # returns the form..
            data = self.prepare(data)

        if dry_run:
            return data

         # Try to upload
        r = self._upload(data)

        if r.status_code == 302:

            log.debug('302 somehting')

        #    return self._upload(data)

    def upload2(self, data):
        """ Takes a dict or media_element"""
        # Check if the torrent already exist on the tracker
        #self.search(data) # fix me

        # Check that we hasnt uploaded that url before, check db

        # _.upload expects a dict
        if not isinstance(data, dict):
            data = self.prepare(data)

        return data

    def prepare(self, media_element, categories=None, comment=None):
        """ Prepare for upload

            Makes a torrent and gets media info to fill out the upload form

            Arg:
                media_element (class, dict),
                categories (dict)
                comment (str)

            Return all the data needed for a correct upload form
        """
        # Allow
        if categories is None and not self.categories:
            self.categories = self._build_categories()
            log.debug(pp(self.categories))

        torrent_info, save_path = media_element.to_torrent()

        if media_element.type in ['video', 'episode', 'movie']:

            me = media_element.extract()
            # This would be the file name or the foldername
            filename = os.path.basename(me['filepath'])

            self.uploadform['mediainfo'] = (None, me['media_info']['raw_string'])
            self.uploadform['name'] = (None, filename)

            # Find the main category
            main_cat = None
            if me['type'] == 'movie':
                main_cat = self.categories['kategori']['filmer']
            elif me['type'] == 'episode':
                main_cat = self.categories['kategori']['tv']

            self.uploadform['main'] = (None, main_cat)
            #http://download.openbricks.org/sample/
            # If we failt to get the correct params always fall back to annet.
            if me['media_info']['Video']['Format'] == 'AVC':  # h.254
                self.uploadform['sub_1'] = (None, self.categories.get('codec', {}).get('h.264', '24'))

            elif me['media_info']['Video']['Codec ID'] == 'XVID':  #or format: MPEG-4 Visual
                self.uploadform['sub_1'] = (None, self.categories.get('codec', {}).get('xvid', '24'))

            elif me['media_info']['Video']['Format'] == 'MPEG Video':
                self.uploadform['sub_1'] = (None, self.categories.get('codec', {}).get('mpeg', '24'))

            elif me['media_info']['Video']['Format'] == 'VC-1':
                self.uploadform['sub_1'] = (None, self.categories.get('codec', {}).get('vc-1', '24'))

            elif re.findall(r'(VP\d)', me['media_info']['Video']['Format']):
                self.uploadform['sub_1'] = (None, '14')

            elif me['container'] == 'wmv':
                self.uploadform['sub_1'] = (None, self.categories.get('codec', {}).get('wmv', '24'))

            else:
                self.uploadform['sub_1'] = (None, self.categories.get('codec', {}).get('annet', '24'))

            # Kvalitet
            me_v_height = int(me['media_info']['Video']['Height'].replace('pixels', '').replace(' ', ''))

            if me_v_height > 720:
                self.uploadform['sub_2'] = (None, self.categories.get('kvalitet', {}).get('HD-1080p/i', '19'))
            elif me_v_height == 720:
                self.uploadform['sub_2'] = (None, self.categories.get('kvalitet', {}).get('HD-720p', '20'))
            else:
                self.uploadform['sub_2'] = (None, self.categories.get('kvalitet', {}).get('SD', '22'))

            # try to find medium/source
            # I hope guessit can handle this in the future
            # checkout how to manually add rebulk to guessit
            filename = filename.lower()
            if any([z for z in ['-remux', '-mux', 'remux'] if z in filename]):
                medium = 'remux'

            elif any([z for z in ['encode', 'dvdrip', 'hddvdrip', 'dvd-rip'] if z in filename]):
                medium = 'encode'

            elif any([z for z in ['bluray', 'blu-ray'] if z in filename]):
                medium = 'blu-ray'

            elif 'capture' in filename: # add more like ts?
                medium = 'capture'

            else:
                medium = me.get('format', '').lower()
            self.uploadform['sub_3'] = (None, self.categories.get('medium', {}).get(medium, '34'))

            # Add nfo if it exist
            log.debug('media_element.has_nfo', media_element.has_nfo)
            if media_element.has_nfo:
                self.uploadform['nfo'] = (os.path.basename(media_element.has_nfo),
                                          open(media_element.has_nfo).read(),
                                          'application/octet-stream')

            # Lets see if we can find a image description from imdb
            get_imdb_url = imdb_aka(me['title'])
            if get_imdb_url:
                # The closest match is the first one, if we dont get it
                # we want to skip it.
                first_hit = get_imdb_url[0]
                if first_hit.get('type') == me['type'] and me['title'] == first_hit.get('name', ''):
                    self.uploadform['infourl'] = 'http://www.imdb.com/title/%s' % first_hit.get('imdbid', '')

        if media_element.type in ['audio', 'song', 'album']:
            pass

        #if comment:  # fixme
        self.uploadform['descr'] = (None, "test upload from https://github.com/Hellowlol/AutoUp, do not publish") #(None, comment)

        self.uploadform['file'] = (media_element.torrent_name, open(save_path, 'rb').read(), 'application/x-bittorrent')
        #print pp(self.uploadform)

        return self.uploadform

    def _upload(self, data=None):
        response = self.fetcher(self.norbits_upload_url, action='post', files=data)
        print(self._was_upload_ok(response))
        return response

    def _was_upload_ok(self, html_upload_response):
        """ Parses the html reseponse of the upload and tries to figure out if it was successfull or not

            Also calls the db to report the stats

        """
        if html_upload_response.status_code == 302:
            print('upload ok..')
            pass # this is ok, call db
        else:

            html_upload_response = html_upload_response.text
            # See html file, xpath for ok: //*[@id="content"]/div[2]
            # ok:  #content > div:nth-child(7) > h3
            # error: # #taDiv > div
            site = bs(html_upload_response.encode('latin-1'), 'html5lib')

            err = site.select('#taDiv > div')
            for e in err:
                print(e.get_text())# todo

        #Check for error

    def search(self, q):
        category = {'all': 0,
                    'movies': 1,
                    'music': 5,
                    'tv': 2,
                    'software': 3,
                    'games': 4,
                    'books': 6}

        payload = {'username': self.username,
                   'passkey': self.apikey,
                   'search': str(q),
                   'limit': 3000
        }

        try:
            result = requests.post('https://norbits.net/api2.php?action=torrents', json=payload)
            results = result.json()
            return results
        except Exception as e:
            pass

    def _build_categories(self):
        """ Parses norbits browse site to get all the categories as a nested dict """

        log.error('Make cats')
        html = self.fetcher(self.norbits_cat_url)
        site = bs(html.text.encode('utf-8'), "html5lib")

        all_cats = {}
        #            # main            #subcat_1       # subcat_2      #subcat_3
        wanted_ids = ['kategori_boxes', 'codec_boxes', 'medium_boxes', 'kvalitet_boxes']

        for _id in wanted_ids:
            cat_dict = {}
            categories = site.find_all(id=_id)
            for c in categories:
                links = c.find_all('a')
                for l in links:
                    cat_dict[l.text.lower()] = l.attrs['href'].split('=')[1]
                    all_cats[_id.split('_')[0]] = cat_dict

        return all_cats


#NB = Norbits()
#NB.login()
#NB._upload()


