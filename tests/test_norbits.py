#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from os.path import abspath
import os
import glob


sys.path.insert(0, os.path.abspath('..'))

cp = abspath('.')

from core.mediaelements import Video, Audio
from core.sites.norbits import Norbits
from core.helpers import dict_compare

# hardcorded cats so we dont need to login.
cat = {
    'codec': {
        'aac': '18',
        'annet': '24',
        'flac': '16',
        'h.264': '9',
        'm4b': '36',
        'mp3': '15',
        'mpeg-2': '11',
        'ogg vorbis': '17',
        'vc-1': '35',
        'vp': '14',
        'wmv': '13',
        'xvid': '10'
    },
    'kategori': {
        'filmer': '1',
        'lydbøker': '7',
        'musikk': '5',
        'musikkvideoer': '8',
        'podcasts': '40',
        'programmer': '3',
        'spill': '4',
        'tidsskrift': '6',
        'tv': '2'
    },
    'kvalitet': {
        '192': '42',
        '256': '43',
        '320': '44',
        'hd-1080p/i': '19',
        'hd-720p': '20',
        'lossless': '46',
        'sd': '22',
        'vbr': '45'
    },
    'medium': {
        'annet': '34',
        'aviser': '39',
        'blader': '38',
        'blu-ray': '27',
        'capture': '28',
        'cd': '31',
        'dvd': '26',
        'e-bøker': '37',
        'encode': '29',
        'kasett': '41',
        'remux': '48',
        'vinyl': '32',
        'web': '33',
        'web-dl': '47'
    }
}


def test_login():
    pass

def test_form_build():
    pass

def test_audio_element():
    pass



def test_video_elements():

    matches = []
    for root, dirnames, filenames in os.walk(os.path.join(cp, 'samples')):
        for filename in filenames:
            matches.append(os.path.join(root, filename))

    for f in sorted(matches):
        print f

def test_video_element():
    v = Video(os.path.join(cp, 'samples', 'The Last Ship S02E01 1080p Blu-ray Remux AVC TrueHD 5.1.mkv'))
    # Test the form, exluded the files.
    n = Norbits().prepare(v, cat)
    x = {'MAX_FILE_SIZE': '3145728',
         'nfopos': (None, 'top'),
         'infourl': (None, 'http://www.imdb.com/title/tt2402207'),
         'name': (None, 'The Last Ship S02E01 1080p Blu-ray Remux AVC TrueHD 5.1.mkv'),
         'descr': (None, 'test upload from https://github.com/Hellowlol/AutoUp, do not publish'),
         'nfo': (None, '', 'application/octet-stream'),
         'sub_2': (None, '20'),
         'sub_3': (None, '48'),
         'sub_1': (None, '24'),
         'main': (None, '2')}
    del n['file']
    del n['mediainfo']

    assert dict_compare(n, x) is True




#test_video_elements()
#test_video_element()


