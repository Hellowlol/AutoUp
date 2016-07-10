from qbittorrent import Client as q_client
from core.clients import Client


class Qbittorrent(Client):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.username = kwargs.get('username', 'admin')
        self.password = kwargs.get('password', '123456')
        self.url = kwargs.get('url', 'http://127.0.0.1:7777/')

        self.qb = q_client(self.url)
        self.qb.login(username=self.username, password=self.password)

    def download_torrent(self, torrent, save_path, label=''):
        """ Add a torrent to the torrent client

            Args:
                torrent (str, list): torrent is a filepath or url
                save_path (str): The root save path downloaded file/s
                label (str): Label to add to download client

            Returns:
                Ok regardsless if fails or not
        """
        if any(i for i in ['http', 'magnet:', 'bc://bt/'] if torrent.startswith(i)):
            return self.qb.download_from_link(torrent, save_path=save_path, label=label)

        if ',' in torrent:  # Assume its a sting, , should never be in a fp anyway
            torrent = [open(t, 'rb') for t in torrent.split(',')]
        else:
            torrent = open(torrent, 'rb')

        return self.qb.download_from_file(torrent, save_path=save_path, label=label)

    def get_torrents(self, **kwargs):
        r = self.qb.torrents(status='all', limit=9999, **kwargs)
        return r

    def get_torrents_for_tracker(self, annonce_url):
        filtered_torrents = []
        torrents = self.get_torrents()
        avg_ul = 0
        avg_dl = 0
        cur_ul = 0
        cur_dl = 0
        seed_time = 0
        total_uploaded = 0
        total_download = 0
        for torrent in torrents:
            tracker = self.qb.get_torrent_trackers(torrent['hash'])
            for z in tracker:
                if annonce_url in z.get('url'):
                    t = self.qb.get_torrent(torrent['hash'])
                    # Add to torrent site spesific
                    avg_dl += t.get('dl_speed_avg', 0)
                    avg_ul += t.get('ul_speed_avg', 0)
                    cur_dl += t.get('dl_speed', 0)
                    cur_ul += t.get('up_speed', 0)
                    seed_time += t.get('seeding_time', 0)
                    total_uploaded += t.get('total_uploaded', 0)
                    total_download += t.get('total_download', 0)

                    # combine them
                    torrent['tracker'] = tracker
                    torrent['details'] = t
                    filtered_torrents.append(torrent)

        return {'avg_ul': avg_ul,
                'avg_dl': avg_dl,
                'cur_ul': cur_ul,
                'seed_time': seed_time,
                'total_uploaded': total_uploaded,
                'total_download': total_download,
                'torrents': filtered_torrents}







if __name__ == '__main__':
    import time
    from pprint import pprint
    start = time.time()
    x = Qbittorrent(username='admin', password='123456')
    print pprint(x.get_torrents_for_tracker('https://www.norbits.net'))
    print(time.time() - start)
