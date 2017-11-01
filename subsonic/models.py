import typing


class MusicFolder(object):
    def __init__(self, _id: str, name: str):
        self.id = _id
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'MusicFolder<id[{0}], name[{1}]>'.format(self.id, self.name)


class Index(object):
    def __init__(self, name: str, artist: typing.List[MusicFolder]):
        self.name = name
        self.artist = artist

    def __repr__(self):
        return 'Index<name[{0}], artist[{1}]>'.format(self.name, self.artist)


class Child(object):
    def __init__(self, id_: str, is_dir: bool, title: str, album: str, artist: str, track: int, genre: str, size: int,
                 content_type: str,
                 suffix: str,
                 duration: int,
                 bit_rate: int,
                 path: str,
                 play_count: int,
                 created: str,
                 album_id: str,
                 artist_id: str,
                 type_: str):
        self.id = id_
        self.is_dir = is_dir
        self.title = title
        self.album = album
        self.artist = artist
        self.track = track
        self.genre = genre
        self.size = size
        self.content_type = content_type
        self.suffix = suffix
        self.duration = duration
        self.bit_rate = bit_rate
        self.path = path
        self.play_count = play_count
        self.created = created
        self.album_id = album_id
        self.artist_id = artist_id
        self.type = type_

    def __repr__(self):
        return 'Child<id[{0}], title[{1}]>'.format(self.id, self.title)


class IndexRoot(object):
    def __init__(self, last_modified: int, ignored_articles: str, index: typing.List[Index], child: typing.List[Child]):
        self.last_modified = last_modified
        self.ignored_articles = ignored_articles
        self.index = index
        self.child = child

    def __repr__(self):
        return 'IndexRoot<len(Index)={0} len(Child)={1}>'.format(len(self.index), len(self.child))


class Song(Child):
    pass


class Album(object):
    def __init__(self, id_: str, name: str, cover_art: str, song_count: int, created: str, duration: int, artist: str,
                 artist_id: str, songs: typing.List[Song]):
        self.id = id_
        self.name = name
        self.cover_art = cover_art
        self.song_count = song_count
        self.created = created
        self.duration = duration
        self.artist = artist
        self.artist_id = artist_id
        self.songs = songs

    def __repr__(self):
        return 'Album<id[{0}], name[{1}], artist[{2}]>'.format(self.id, self.name, self.artist)


class Artist(object):
    def __init__(self, id_: str, name: str, cover_art: str, album_count: int, albums: typing.List[Album]):
        self.id = id_
        self.name = name
        self.cover_art = cover_art
        self.album_count = album_count
        self.albums = albums

    def __repr__(self):
        return 'Artist<id[{0}], name[{1}], album_count[{2}]>'.format(self.id, self.name, self.album_count)


class ArtistIndex(object):
    def __init__(self, name: str, artists: typing.List[Artist]):
        self.name = name
        self.artists = artists

    def __repr__(self):
        return 'ArtistIndex<name[{0}], len(Artists)={1}>'.format(self.name, len(self.artists))


class Directory(object):
    def __init__(self, id_: str, name: str, child: typing.List[Child]):
        self.id = id_
        self.name = name
        self.child = child

    def __repr__(self):
        return 'Directory<id[{0}], name[{1}], len(Child)={2}>'.format(self.id, self.name, len(self.child))
