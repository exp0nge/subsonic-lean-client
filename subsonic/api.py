import hashlib
import random
import typing
import logging
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
import tortilla

import models

logger = logging.getLogger(__name__)


class ListTypes(object):
    RANDOM = 'random'
    NEWEST = 'newest'
    HIGHEST = 'highest'
    FREQUENT = 'frequent'
    RECENT = 'recent'
    ALPHABETICAL_NAME = 'alphabeticalByName'
    ALPHABETICAL_ARTIST = 'alphabeticalByArtist'
    STARRED = 'starred'
    BY_YEAR = 'byYear'
    BY_GENRE = 'byGenre'


class SubsonicClient(object):
    API_VERSION = '1.16.0'

    def __init__(self, username, password, server_location, app_name='cloudplayer', debug_log=False):
        self.username = username
        self.password = password
        self.app_name = app_name
        self.server_location = server_location
        self.api = tortilla.wrap('{0}/rest'.format(server_location))

        self.validate()

        logger.info("Logged in as {0}".format(self.username))

    @property
    def _auth(self) -> dict:
        salt = str(random.getrandbits(64))
        hashed_password = hashlib.md5(self.password.encode() + salt.encode()).hexdigest()
        return {'u': self.username, 't': hashed_password, 's': salt}

    @property
    def __metadata(self) -> dict:
        return {'v': SubsonicClient.API_VERSION, 'c': self.app_name, 'f': 'json'}

    def _merge_params(self, params: dict = None) -> dict:
        return {**self._auth, **self.__metadata, **(params if params else {})}

    def _request_get(self, route, params: dict = None) -> dict:
        full_params = self._merge_params(params)
        result = route.get(params=full_params)['subsonic-response']
        if result['status'] == 'failed':
            raise ValueError(result['error']['message'])
        return result

    def _make_child(self, child: dict) -> models.Child:
        return models.Child(child['id'],
                            child['isDir'],
                            child['title'],
                            child.get('album'),
                            child.get('artist'),
                            child.get('track'),
                            child.get('genre'),
                            child.get('size'),
                            child.get('contentType'),
                            child.get('suffix'),
                            child.get('duration'),
                            child.get('bitRate'),
                            child.get('path'),
                            child.get('playCount'),
                            child.get('created'),
                            child.get('albumId'),
                            child.get('artistId'),
                            child.get('type'))

    def validate(self) -> None:
        self._request_get(self.api.ping)

    def get_music_folders(self) -> typing.List[models.MusicFolder]:
        all_folders = self._request_get(self.api.getMusicFolders)['musicFolders']['musicFolder']
        return [models.MusicFolder(folder['id'], folder.get('name', '')) for folder in all_folders]

    def get_music_directory(self, id_: str):
        items = self._request_get(self.api.getMusicDirectory(), params={'id': id_})['directory']
        if 'child' in items:
            return models.Directory(items['id'], items['name'], [self._make_child(child) for child in items['child']])
        else:
            return models.Directory(items['id'], items['name'], [])

    def _process_index(self, indexes: dict, indices: list) -> None:
        for index in indexes['index']:
            artists = []
            for artist in index['artist']:
                artists.append(models.MusicFolder(artist['id'], artist['name']))
            indices.append(models.Index(index['name'], artists))

    def get_indexes(self, music_folder_id: int = None, if_modified_since: int = None) -> typing.Optional[
        models.IndexRoot]:
        params = {}
        if music_folder_id:
            params['musicFolderId'] = music_folder_id
        if if_modified_since:
            params['ifModifiedSince'] = if_modified_since
        indexes = self._request_get(self.api.getIndexes)['indexes']
        indices = []
        children = []
        if 'index' not in indexes:
            return None

        self._process_index(indexes, indices)

        if 'child' in indexes:
            for child in indexes['child']:
                children.append(self._make_child(child))
        return models.IndexRoot(indexes['lastModified'], indexes['ignoredArticles'], indices, children)

    def get_artists(self, music_folder_id: str = None) -> typing.List[models.ArtistIndex]:
        params = {'id': music_folder_id} if music_folder_id else {}
        items = self._request_get(self.api.getArtists(), params=params)['artists']
        artist_indices = []
        for index in items['index']:
            artist_indices.append(models.ArtistIndex(index['name'],
                                                     [models.Artist(index_artist['id'],
                                                                    index_artist['name'],
                                                                    index_artist.get('coverArt'),
                                                                    index_artist['albumCount'],
                                                                    []) for index_artist in
                                                      index['artist']]))

        return artist_indices

    def get_artist(self, id_: str) -> models.Artist:
        items = self._request_get(self.api.getArtist(), params={'id': id_})['artist']
        return models.Artist(items['id'], items['name'], items.get('coverArt'), items.get('albumCount'),
                             [models.Album(album['id'],
                                           album['name'],
                                           album.get('coverArt'),
                                           album['songCount'],
                                           album['created'],
                                           album['duration'],
                                           album['artist'],
                                           album['artistId'],
                                           []) for album in items['album']])

    def get_album(self, id_: str) -> models.Album:
        items = self._request_get(self.api.getAlbum(), params={'id': id_})['album']
        return models.Album(items['id'], items['name'], items.get('coverArt'), items['songCount'],
                            items['created'],
                            items['duration'],
                            items.get('artist'),
                            items.get('artistId'),
                            [models.Song(child['id'],
                                         child['isDir'],
                                         child['title'],
                                         child['album'],
                                         child['artist'],
                                         child.get('track'),
                                         child.get('genre'),
                                         child['size'],
                                         child['contentType'],
                                         child['suffix'],
                                         child['duration'],
                                         child['bitRate'],
                                         child['path'],
                                         child['playCount'],
                                         child['created'],
                                         child['albumId'],
                                         child['artistId'],
                                         child['type']) for child in items['song']])

    def private_stream_url(self, id_: str) -> str:
        qs = urlencode(self._merge_params(params={'id': id_}))
        return '{0}/{1}/stream?{2}'.format(self.server_location, 'rest', qs)

    def create_share(self, id_: str, description: str = None, expires: int = None) -> typing.List[models.Share]:
        params = {'id': id_}
        if description:
            params['description'] = description
        if expires:
            params['expires'] = expires

        shares = self._request_get(self.api.createShare(), params=params)['shares']['share']
        return [models.Share(share['id'], share['url'], share['username'], share['created'], share['expires'],
                             share['visitCount'],
                             [self._make_child(child) for child in share['entry']]) for share in shares]

    def get_album_list(self, type_: str, size: int = 10, offset: int = 0, from_year: int = None,
                       to_year: int = None, genre: int = None, music_folder_id: int = None) -> typing.List[
        models.Album]:
        params = {'type': type_, 'size': size, 'offset': offset}

        if type_ == ListTypes.BY_YEAR and (from_year is None or to_year is None):
            raise ValueError('from_year and to_year required with byYear type')
        else:
            params['fromYear'] = from_year
            params['toYear'] = to_year
        if type_ == ListTypes.BY_GENRE and genre is None:
            raise ValueError('genre required with byGenre type')
        else:
            params['genre'] = genre

        if music_folder_id:
            params['musicFolderId'] = music_folder_id

        albums = self._request_get(self.api.getAlbumList(), params=params)['albumList']

        if 'album' not in albums:
            return []

        albums = albums['album']

        return [models.Album(album['id'], album['title'], album.get('coverArt'), album.get('songCount'),
                             album['created'],
                             album.get('duration'),
                             album.get('artist'),
                             album.get('artistId'),
                             []) for album in albums]

    def _check_children(self, children: list, explored: typing.List[str]) -> typing.List[models.Song]:
        all_songs = []
        for child in children:
            if isinstance(child, list):
                for inner_child in child:
                    if inner_child.is_dir:
                        all_songs.extend(self.get_all_songs_for_id(inner_child.id, explored))
                    else:
                        all_songs.append(child)
            else:
                if child.is_dir:
                    all_songs.extend(self.get_all_songs_for_id(child.id, explored))
                all_songs.append(child)
        return all_songs

    def get_all_songs_for_id(self, id_: str, explored: typing.List[str]) -> typing.Set[models.Song]:
        if id_ in explored:
            print('dup id', id_)
            return set()

        music_dir = self.get_music_directory(id_)
        explored.append(music_dir.id)
        all_songs = self._check_children(music_dir.children, explored)
        return set(all_songs)

    def get_all_songs(self) -> typing.Set[models.Song]:
        root_index = self.get_indexes()
        explored = []
        all_songs = self._check_children(root_index.children, explored)

        print(len(all_songs))

        for root_index in root_index.indices:
            for artist in root_index.artists:
                all_songs.extend(self.get_all_songs_for_id(artist.id, explored))
                print(len(all_songs))
        logger.info("{0} tracks discovered, {1} directories explored".format(len(all_songs), explored))
        return set(all_songs)

    def start_scan(self) -> models.ScanStatus:
        scan_status = self._request_get(self.api.startScan())['scanStatus']
        return models.ScanStatus(scan_status['scanning'], scan_status['count'])

    def get_scan_status(self) -> models.ScanStatus:
        scan_status = self._request_get(self.api.getScanStatus())['scanStatus']
        return models.ScanStatus(scan_status['scanning'], scan_status['count'])

    def search_query(self, query: str, artist_count: int = 20, artist_offset: int = 0, album_count: int = 20,
                     album_offset: int = 0, song_count: int = 20, song_offset: int = 0,
                     music_folder_id: str = None) -> typing.List:
        params = {'query': query, 'artistCount': artist_count, 'artistOffset': artist_offset,
                  'albumCount': album_count, 'albumOffset': album_offset, 'songCount': song_count,
                  'songOffset': song_offset}
        if music_folder_id:
            params['musicFolderId'] = music_folder_id
        results = self._request_get(self.api.search2(), params=params)
        for result in results['searchResult2']:
            raise NotImplementedError()

    def get_all_songs_fast(self) -> typing.Iterator[models.Song]:
        with requests.Session() as session:
            login = session.post('{0}/j_acegi_security_check'.format(self.server_location),
                                 data={'j_username': self.username, 'j_password': self.password})
            if '?error' in login.url:
                raise ValueError("Username or password is wrong")

            q = session.post('{0}/db.view'.format(self.server_location),
                             data={'query': "select count(id) from media_file where type = 'MUSIC';"})

            soup = BeautifulSoup(q.text, 'html.parser')
            table = soup.find('table', attrs={'class': 'ruleTable'})
            if not table:
                return
            max_length = int(table.find('td', attrs={'class': 'ruleTableCell'}).text)
            last_id = -1
            songs_processed = 0
            limit_rows = 5000
            db_columns = ['id', 'title', 'album', 'artist', 'track_number', 'genre', 'file_size',
                          'duration_seconds', 'bit_rate', 'path', 'play_count', 'created', 'format',
                          'album_artist', 'year', 'parent_path', 'variable_bit_rate']

            def _cast_to_int(column):
                try:
                    return int(column)
                except ValueError:
                    return None

            while songs_processed < max_length:
                q = session.post('{0}/db.view'.format(self.server_location), data={
                    'query': "select {0} from media_file where type = 'MUSIC' and id > {1} limit {2};".format(
                        ','.join(db_columns),
                        last_id,
                        limit_rows)})
                soup = BeautifulSoup(q.text, 'html.parser')

                table = soup.find('table', attrs={'class': 'ruleTable'})
                if table is None:
                    return
                for tr in table.find_all('tr')[1:]:
                    columns = [col.text for col in tr.find_all('td')]
                    song = models.Song(id_=columns[0], is_dir=False, title=columns[1], album=columns[2],
                                       artist=columns[3], track=_cast_to_int(columns[4]), genre=columns[5],
                                       size=_cast_to_int(columns[6]), duration=_cast_to_int(columns[7]),
                                       content_type='MUSIC', suffix='', bit_rate=_cast_to_int(columns[8]),
                                       path=columns[9], play_count=_cast_to_int(columns[10]), created=columns[11],
                                       file_format=columns[12], album_artist=columns[13],
                                       year=_cast_to_int(columns[14]), parent_path=columns[15],
                                       variable_bit_rate=columns[16].lower() == 'true' if columns[16] else None,
                                       stream_url=self.private_stream_url(columns[0]), album_id='', artist_id='',
                                       type_='FILE')
                    yield song
                    last_id = _cast_to_int(columns[0])
                    songs_processed += 1
                print(last_id)
