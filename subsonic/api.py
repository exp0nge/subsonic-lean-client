import hashlib
import random
import typing
import logging
from urllib.parse import urlencode

import tortilla

import models

logger = logging.getLogger(__name__)


class SubsonicClient(object):
    API_VERSION = '1.16.0'

    def __init__(self, username, password, server_location, app_name='cloudplayer', debug_log=False):
        self.username = username
        self.password = password
        self.app_name = app_name
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
                            child['artist'],
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

    def get_indexes(self, music_folder_id: int = None, if_modified_since: int = None) -> models.IndexRoot:
        params = {}
        if music_folder_id:
            params['musicFolderId'] = music_folder_id
        if if_modified_since:
            params['ifModifiedSince'] = if_modified_since
        indexes = self._request_get(self.api.getIndexes)['indexes']
        indices = []
        children = []
        for index in indexes['index']:
            artists = []
            for artist in index['artist']:
                artists.append(models.MusicFolder(artist['id'], artist['name']))
            indices.append(models.Index(index['name'], artists))
        for child in indexes['child']:
            children.append(self._make_child(child))
        return models.IndexRoot(indexes['lastModified'], indexes['ignoredArticles'], indexes['index'], indexes['child'])

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
        return models.Album(items['id'], items['name'], items.get('coverArt'), items['songCount'], items['created'],
                            items['duration'],
                            items.get('artist'),
                            items.get('artistId'),
                            [models.Song(child['id'],
                                         child['isDir'],
                                         child['title'],
                                         child['album'],
                                         child['artist'],
                                         child['track'],
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

    def stream_url(self, _id: str) -> str:
        part = self.api.stream()
        qs = urlencode(self._merge_params(params={'id': _id}))
        return '{0}?{1}'.format(part._url, qs)

    def get_all_songs(self) -> typing.List[models.Song]:
        all_songs = []
        total_songs = 0
        for artist_index in self.get_artists():
            print('processing', artist_index)
            for art in artist_index.artists:
                artist_album_songs = self.get_album(art.id)
                all_songs.extend(artist_album_songs.songs)
                total_songs += artist_album_songs.song_count
        print(total_songs)
        return all_songs


if __name__ == '__main__':
    import os

    logger.setLevel(logging.DEBUG)

    api = SubsonicClient(os.environ['USERNAME'], os.environ['PASSWORD'], os.environ['LOCATION'])
    folders = api.get_music_folders()
    print(folders)
    indexes = api.get_indexes()
    print(indexes)
    artists = api.get_artists()
    print(artists)
    artist = api.get_artist(artists[0].artists[0].id)
    print(artist)
    album_songs = api.get_album(artist.albums[0].id)
    print(album_songs)
    music_directory = api.get_music_directory('6')
    print(music_directory)
    # songs = api.get_all_songs()
    # print(songs)
    # print('len of songs', len(songs))
    stream_url = api.stream_url('84')
    print(stream_url)
