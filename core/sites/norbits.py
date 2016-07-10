#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json
import os
import sys
from pprint import pprint as pp
import re
import logging

from bs4 import BeautifulSoup as bs
import requests

from core.helpers import imdb_aka, upload_to_imgurl, query_predb, make_images_from_video, query_tvdb, get_imdb
from core.database import Database
from core.sites import Site


log = logging.getLogger(__name__)


class Norbits(Site):
    """ Handles all the Norbits shit """

    categories = {}

    def __init__(self, data=None, *args, **kwargs):
        super(self.__class__, self).__init__(data, *args, **kwargs)
        self.norbits_url = 'http://www.norbits.net/upload.php'
        self.norbits_login_url = 'http://www.norbits.net/takelogin.php'
        self.norbits_upload_url = 'http://www.norbits.net/takeupload.php'
        self.norbits_cat_url = 'http://www.norbits.net/browse.php'
        self.session = requests.Session()
        self.login_attempts = 0
        self.site_disabled = False

        # Add a real config
        self.username = kwargs.get('norbits_username', '')
        self.password = kwargs.get('norbits_password', '')
        self.apikey = kwargs.get('norbits_apikey', '')
        self.norbits_comment = kwargs.get('norbits_comment', '')
        # this is a from cli and should override a norbits comment from the cfg
        self.comment = kwargs.get('comment', '')

        if not self.username or not self.password:
            log.warning('Username or password is missing.')

        # Keep
        self.uploadform = {'MAX_FILE_SIZE': '3145728',
                           'file': (None, ''),
                           'name': (None, 'name'),
                           'nfo': (None, '', 'application/octet-stream'),
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

        data = {'username': self.username.encode('utf-8'),
                'password': self.password.encode('utf-8'),
                'returnto': to}

        r = self.session.post(self.norbits_login_url, headers=self.headers, data=data)
        log.info('Tried to login to Norbits %s' % r.status_code)

        html = bs(r.text.encode('latin-1'), 'html5lib')
        s = html.select('#userinfo')

        if len(s):
            log.info('Login Norbits success')
            return True
        else:
            log.info('Login Norbits error')
            False

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
            log.warning('Norbits has been disabled because of %s failed login attemps' % self.login_attempts)
            return

        log.debug('url=%s action=%s status=%s' % (r.url, action, r.status_code))
        # We are not logged in and is taken to the login site
        if (r.status_code == 302 and r.url == 'http://www.norbits.net/takelogin.php' or
            r.status_code == 200 and '/login.php?' in r.url):
            if not self.site_disabled or self.login_attempts > 3:
                self.login_attempts += 1
                if self.login() is True:
                    log.debug('Successfull login to norbits, trying orginal path %s' % path)
                    # Do the same call again
                    return self.fetcher(path, action=action, data=data, files=files)

        return r

    def upload(self, data, dry_run):
        """ Takes a dict or media_element"""
        # _.upload expects a dict
        if not isinstance(data, dict):
            # returns the form..
            data = self.prepare(data)

        if dry_run:
            log.debug('Didnt upload to site because of dry run')
            return data

        # Try to upload
        r = self._upload(data)

        if r.status_code == 302:
            log.debug('302 somehting')
        #    return self._upload(data)

    def prepare(self, media_element, categories=None, comment=None):
        """ Prepare for upload

            Makes a torrent and gets media info to fill out the upload form

            Args:
                media_element (class, dict): shit to build from
                categories (dict): See _build_categories()
                comment (str): 'Get added to the description on norbits'

            Returns:
                 all the data needed for a correct upload form
        """
        desc = ''

        # Allow
        if categories is None and not self.categories:
            categories = self._build_categories()
            #log.debug(pp(self.categories))

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
                main_cat = categories['kategori']['filmer']
            elif me['type'] == 'episode':
                main_cat = categories['kategori']['tv']

            self.uploadform['main'] = (None, main_cat)
            #http://download.openbricks.org/sample/
            # If we failt to get the correct params always fall back to annet.
            if me['media_info']['Video']['Format'] == 'AVC':  # h.254
                self.uploadform['sub_1'] = (None, categories.get('codec', {}).get('h.264', '24'))

            elif me['media_info']['Video']['Codec ID'] == 'XVID':  #or format: MPEG-4 Visual
                self.uploadform['sub_1'] = (None, categories.get('codec', {}).get('xvid', '24'))

            elif me['media_info']['Video']['Format'] == 'MPEG Video':
                self.uploadform['sub_1'] = (None, categories.get('codec', {}).get('mpeg', '24'))

            elif me['media_info']['Video']['Format'] == 'VC-1':
                self.uploadform['sub_1'] = (None, categories.get('codec', {}).get('vc-1', '24'))

            elif re.findall(r'(VP\d)', me['media_info']['Video']['Format']):
                self.uploadform['sub_1'] = (None, '14')

            elif me['container'] == 'wmv':
                self.uploadform['sub_1'] = (None, categories.get('codec', {}).get('wmv', '24'))

            else:
                self.uploadform['sub_1'] = (None, categories.get('codec', {}).get('annet', '24'))

            # Kvalitet
            me_v_height = int(me['media_info']['Video']['Height'].replace('pixels', '').replace(' ', ''))

            if me_v_height > 720:
                self.uploadform['sub_2'] = (None, categories.get('kvalitet', {}).get('HD-1080p/i', '19'))
            elif me_v_height == 720:
                self.uploadform['sub_2'] = (None, categories.get('kvalitet', {}).get('HD-720p', '20'))
            else:
                self.uploadform['sub_2'] = (None, categories.get('kvalitet', {}).get('SD', '22'))

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

            elif 'capture' in filename:  # add more like ts?
                medium = 'capture'

            else:
                medium = me.get('format', '').lower()
            self.uploadform['sub_3'] = (None, categories.get('medium', {}).get(medium, '34'))

            # Add nfo if it exist
            log.debug('media_element.has_nfo %s' % media_element.has_nfo)
            if media_element.has_nfo:
                self.uploadform['nfo'] = (os.path.basename(media_element.has_nfo),
                                          open(media_element.has_nfo).read(),
                                          'application/octet-stream')

            # parse the aka site incase the name is in another language
            aka = imdb_aka(me['title'])
            fixed_imdb_id = None
            if aka:
                # Since this is suppose to be automated we are strict,
                # The closest match is the first one, if we dont get it we want to skip it.
                first_hit = aka[0]
                if first_hit.get('type') == me['type'] and me['title'].lower() == first_hit.get('name', '').lower():

                    gi = get_imdb(imdbid=first_hit.get('imdbid', ''), season=me.get('season'), episode=me.get('episode'))
                    # the correct imdb for that episode
                    fixed_imdb_id = gi[0].imdb_id
                    desc += 'Synopsis %s \n\n[spoiler]%s[/spoiler]\n\n' % (filename, gi[1])

            if fixed_imdb_id:
                self.uploadform['infourl'] = (None, 'http://www.imdb.com/title/%s/' % fixed_imdb_id)

            if media_element.has_images:
                imgz = upload_to_imgurl(media_element.has_images, filename)
                imgz = '\n\n'.join([i for z in imgz for i in z])
                desc += imgz
                # fix me
                #self.uploadform['descr'] = (None, 'test upload from https://github.com/Hellowlol/AutoUp, do not publish test of images' + imgz)

            if me['type'] == 'episode' and query_predb(filename):
                log.info('%s was a found on predb, this is a scene release')

        if media_element.type in ['audio', 'song', 'album']:
            pass  # todo

        self.uploadform['file'] = (media_element.torrent_name, open(torrent_info._filepath, 'rb').read(), 'application/x-bittorrent')

        if desc:
            self.uploadform['descr'] = (None, desc + ' \n\ntest upload from https://github.com/Hellowlol/AutoUp, do not publish test of images')

        #print(self.uploadform['descr'])
        #print(self.uploadform)
        #print pp(self.uploadform)

        return self.uploadform

    def _upload(self, data=None):
        response = self.fetcher(self.norbits_upload_url, action='post', files=data)
        success = self._was_upload_ok(response)
        if success is True:
            # insert in db..
            pass
        else:
            log.error('Upload failed because of %s' % success)
            # add some shit
        return response

    def _was_upload_ok(self, html_upload_response):
        """ Parses the html reseponse of the upload and tries to figure out if it was successfull or not

            Also calls the db to report the stats

        """
        if html_upload_response.status_code == 302 or (html_upload_response.status_code == 200 and
                                                       'http://www.norbits.net/details.php?id=' in html_upload_response.url):
            return True
        else:

            html_upload_response = html_upload_response.text
            # See html file, xpath for ok: //*[@id="content"]/div[2]
            # ok:  #content > div:nth-child(7) > h3
            # error: # #taDiv > div
            site = bs(html_upload_response.encode('latin-1'), 'html5lib')
            err = site.select('#taDiv > div')
            reason = ''.join(list(set([e.get_text().strip() for e in err])))
            if reason:
                return reason
            else:
                log.error(html_upload_response)
                for e in err:
                    log.error(e.get_text())
                return 'Some unknown error'

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

        log.debug('Fetching categories from norbits/browse')
        html = self.fetcher(self.norbits_cat_url)
        print html
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


if __name__ == '__main__':
    import os, sys
    sys.path.insert(0, os.path.abspath('..'))

    #NB = Norbits()
    #NB.login()
    #NB._upload()
