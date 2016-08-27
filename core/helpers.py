import json
import os
import logging
import re
import subprocess
import time
from functools import wraps

from bs4 import BeautifulSoup as bs
import requests
import six.moves.urllib.parse as parse
import concurrent.futures as cf
import itertools

from imgurpython import ImgurClient
import tvdbapi_client
from imdbpie import Imdb
import core

log = logging.getLogger(__name__)
SESSION = requests.Session()




try:
    import lxml
    bestparser = 'lxml'
except ImportError:
    bestparser = 'html5lib'

def timeme(func):
    @wraps(func)
    def inner(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        print('\n\n%s took %s' % (func.__name__, time.time() - start))
        return res
    return inner


@timeme
def imdb_aka(s):
    """ Simple helper function that parses the result from a imdb aka search to find the correct imdbid
        This is only used since alof of the uploaded content is norwegian and
        i couldnt find any other site that has akas without having a id of some kind
    """
    log.debug('Trying to find the correct imdb link for %s' % s)

    result = requests.get('http://akas.imdb.com/find?q=%s&s=all' % parse.quote_plus(s))
    soup = bs(result.text, bestparser)
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
        has_year = re.search(ur'\((\d+)\)', vals)
        if has_year:
            d['year'] = has_year.group()
        res.append(d)

    return res


@timeme
def get_media_info(path, format='dict', media_info_cli=None):
    """ Note this is media info cli """

    if media_info_cli is None:
        media_info_cli = core.CONFIG.MEDIA_INFO_CLI or 'mediainfo'

    cmd = '%s "%s"' % (media_info_cli, path)
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
    #elif format == 'xml':
    #    #return xml.shit # fixme use xmltodict remove ugly @ etc

    return mains


def dict_compare(d1, d2):
    # Credit http://stackoverflow.com/a/18860653
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o: (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    same = set(o for o in intersect_keys if d1[o] == d2[o])

    if len(added) == 0 and len(removed) == 0 and len(modified) == 0:
        return True
    else:
        return {'added': added, 'removed': removed, 'modified': modified, 'same': same}


def upload_to_imgurl(fp, name):
    log.debug('Upload to imgurl %r %r' % (fp, name))

    links = []

    client_id = core.CONFIG.IMGUR_CLIENT_ID or '47d69f063752039' # Should be from config?
    client_secret = core.CONFIG.IMGUR_CLIENT_SECRET or'34b43ca44eb088ed05f0ae1bbf22edcd489589a0'

    if not isinstance(fp, list):
        fp = fp.split(',')

    log.debug('Preparing to upload %s images to imgur anonymously' % len(fp))

    client = ImgurClient(client_id, client_secret)

    for f in fp:
        name = os.path.basename(f)
        config = {'album': None,
                  'name': name,
                  'title': name,
                  'description': ''
                }

        image = client.upload_from_path(f, config=config, anon=True)
        try:
            links.append((name, '[img]' + image['link'] + '[/img]'))
        except:
            pass

    return sorted(links)

def shell(cmd):
    try:
        process = subprocess.Popen(cmd,
                                   shell=False,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=None)

        o, e = process.communicate()

        return o
    except Exception as e:
        pass


def make_images_from_video(f, number_of_images=8, format='jpg', ffmpeg_path=None):
    """ Make a thumb for a video file """

    if ffmpeg_path is None:
        ffmpeg_path = core.CONFIG.FFMPEG or 'ffmpeg'

    def make_image(f, ts, i, save_path, format, ffmpeg_path):
        """Makes images from movies """

        s = 'image%s.%s' % (i, format)
        outfile = os.path.join(save_path, s)
        t = time.strftime('%H:%M:%S', time.gmtime(ts * 60))

        cmd = '%s -ss %s -nostats -loglevel 0 -i "%s" -vf select="eq(pict_type\,I)" -q:v 2 -vframes 1 "%s"' % (core.CONFIG.FFMPEG, t, f, outfile)

        process = subprocess.Popen(cmd,
                                   shell=False,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=None)

        o, e = process.communicate()

        if os.path.exists(outfile):
            return outfile

    number_of_images += 2
    time_frames = []

    duration = get_media_info(f)

    duration = float(duration['Video']['Duration'].replace(' min', ''))

    slot = duration / number_of_images

    save_image_path = os.path.dirname(f)

    for z in range(number_of_images - 1):
        duration = duration - slot
        time_frames.append(duration)

    # remove first and last images since its prob junk
    imgz = []
    for i, ts in enumerate(time_frames[1:-1]):
        imgz.append(make_image(f, ts, i, save_image_path, format, ffmpeg_path))

    r = filter(None, imgz)
    return r

#make_images_from_video('C:\htpc\upload1\Billions.S01E02.720p.WEB-DL-NTb\Billions.S01E02.720p.WEB-DL-NTb.mkv')


def parse_predb(html, raw=False):
    all_results = []
    cc = 'pl-body' if raw else 'jsload'

    sr = html.find_all(class_=cc)

    for s in sr:  # div .pl-body or jsload
        for ss in s:  # div .post
            for sss in ss:  # div .p-head
                t = sss.find_all('span', attrs={'data': True})[0].get('data', 0)
                cats = [c.text for c in sss.find_all('span', class_='p-cat')[0]]
                name = sss.find_all('h2')[0].text

                d = {'time': t,
                     'categories': cats,
                     'name': name}

                all_results.append(d)

    return all_results


def check_predb(url=None, raw=None):
    if raw:
        return parse_predb(bs(raw, bestparser))

    r = SESSION.get(url)
    if r.status_code == 503:
        log.debug('We are going to fast, slow down and try again')
        # we are going to fast
        time.sleep(0.4)
        return check_predb(url)

    return parse_predb(bs(r.text, bestparser))


@timeme
def query_predb(search=None, check_all=False, async=False):
    """ Query predb to see if something is in the predb

        Args:

            search(str): what to search

            check_all(bool): Check every page instead of just the first one
            async(bool): Query each url async, kinda useless atm

        Returns:
                bool
    """
    log.debug('Searching predb for %s' % search)

    q_search = parse.quote_plus(search)
    r = requests.get('http://predb.me/?search=%s' % q_search)
    t = []
    # Check every pages.. takes alot of time
    if check_all is True:
        html = bs(r.text, bestparser)
        try:
            pagelist = html.find_all(class_='last-page')[0]
            pages = pagelist.get('href').split('=')[-1]
        except IndexError:
            # there is only one page result but we add two
            pages = 2

        log.debug('predbme had %s pages' % len(pages))

        urls = ['http://predb.me/?search=%s&page=%s&jsload=1' % (q_search, z) for z in range(1, int(pages))]
        # async is useless since we just get blocked with 503
        if async is True:
            with cf.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_url = {executor.submit(check_predb, url): url for url in urls}
                for future in cf.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        data = future.result()
                        t.extend(data)
                    except Exception as exc:
                        print('%r generated an exception: %s' % (url, exc))

        else:
            for url in urls:
                t.extend(check_predb(url))
    else:
        t.extend(check_predb(raw=r.text))

    for srr in itertools.chain(t):
        if srr.get('name') == search:
            return True
    return False




#print query_predb('test', check_all=True, async=True)

@timeme
def query_tvdb(name=None, id=None, imdbId=None, zap2itId=None, season=None, episode=None):
    # fuck this use tvmaze..

    client = tvdbapi_client.get_client(apikey='C614040AE87171D0', username='autoup', userpass='A80D10B8022EBDFE')
    log.debug('Quering tvdb for name=%s imdbid=%s' % (name, imdbId))

    if id:
        if season and episode:
            try:
                return client.get_episodes(id, airedSeason=season, airedEpisode=episode)[0]
            except:
                return {}
        else:
            return client.get_series(id)

    else:
        try:
            loc = locals().copy()

            del loc['season']
            del loc['episode']
            print loc
            c = client.search_series(**loc)

            if season is None and episode is None:
                return c

            if name:
                if len(c) > 1:
                    raise ValueError('To many shows.. try searching using a id')
                else:
                    id = c[0].get('id')
            else:

                id = c[0].get('id')
                tt = client.get_episodes(id, airedSeason=season, airedEpisode=episode)[0]
                import pprint
                print pprint.pprint(tt)
                return client.get_episodes(id, airedSeason=season, airedEpisode=episode)[0]

        except Exception as e:
            print(e)
            return {}


@timeme
def get_imdb(imdbid=None, season=None, episode=None, cache=False, anonymize=False):
    """ use this """

    imdb = Imdb(anonymize=anonymize, cache=cache)
    if season is None or episode is None:
        z = imdb.get_title_by_id(imdbid)
        return (z, z.plot_outline)

    for ep in imdb.get_episodes(imdbid):
        if ep.season == season and ep.episode == episode:
            return (ep, imdb.get_title_plots(ep.imdb_id)[0])

#print test_imdb(imdbid='tt1796960', season=1, episode=1)
#print get_imdb(imdbid='tt0450232')
#print get_imdb(imdbid='tt4270492', season=1, episode=2)
#print query_tvdb(imdbId='tt1796960', season=1, episode=2)
#make_images_from_video(r'C:\htpc\upload5\Kaptein Sabeltann og skatten i Kjuttaviga\Kaptein.Sabeltann.og.skatten.i.Kjuttaviga.WEBDL-nrkdl.mkv')

if __name__ == '__main__':
    pass
    #upload_to_imgurl(['C:\htpc\upload3\Colony.S01E10.1080p.WEB.DL-VietHD-thumb.jpg', 'C:\htpc\upload3\Colony.S01E10.1080p.WEB.DL-VietHD-thumb.jpg'], 'torrentname')