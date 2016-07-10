# utils
import json
import subprocess
import requests
from bs4 import BeautifulSoup as bs
import re

from urllib import quote_plus # fix for py3 plx

def load_secret_file(key, path='C:\\htpc\\password_list.json'):
    with open(path, 'r') as p:
        r = json.load(p)
        if key in r:
            return r.get(key)


def imdb_aka(s):
    # http://akas.imdb.com/find?q=the+blacklist&s=all
    result = requests.get('http://akas.imdb.com/find?q=%s&s=all' % quote_plus(s))
    soup = bs(result.text, 'html5lib')
    res = []

    s = soup.find_all(class_='result_text')
    for trs in s:
        d = {}
        link = trs.find_all('a')[0].get('href', '')
        d['link'] = link

        # find the imdb id
        id_ = re.search(ur'(tt\d+)', link)
        if id_:
            d['imdbid'] = id_.group()
        else:
            d['imdbid'] = ''

        vals = trs.get_text()
        if '(TV Series)' in vals:
            d['type'] = 'episode'
        else:
            d['type'] = 'movie'

        if '[' in vals:
            name = vals.split('[', 1)[0].strip()
        elif '(' in vals:
            name = vals.split('(', 1)[0].strip()
        else:
            name = vals.strip()

        d['name'] = name
        has_year = re.search(ur'(\d+)', vals)
        if has_year:
            d['year'] = has_year.group()

        res.append(d)

    #print('ret', res)
    return res

#imdb_aka('the blacklist')


def get_media_info(path, format='dict'):
    """ Note this is media info cli """
    cmd = 'C:\\Users\\steffen\\Downloads\\MediaInfo_CLI_0.7.87_Windows_i386\\mediainfo "%s"' % (path)
    process = subprocess.Popen(cmd,
                               shell=False,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=None)

    o, e = process.communicate()

    if format == 'raw':
        return o

    mains = {}
    o = o.decode('utf-8')  # py3
    # make a dict of it
    for l in o.splitlines()[:-1]:
        if ':' not in l and l != '':
            # We assume this is main keys
            cat = l.strip('\r')
            mains[cat] = ''
            sub = {}
        elif l == '':
            mains[cat] = sub
        elif ':' in l:
            z = l.split(':', 1)
            k = z[0].strip('\r').strip()
            v = z[1].strip('\r').strip()
            sub[k] = v

    mains['raw_string'] = o

    if format == 'json':
        return json.dumps(mains)

    return mains
