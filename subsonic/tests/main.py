import os
from timeit import Timer

from api import SubsonicClient, ListTypes

if __name__ == '__main__':
    api = SubsonicClient(os.environ['USERNAME'], os.environ['PASSWORD'], os.environ['LOCATION'])
    # folders = api.get_music_folders()
    # print(folders)
    # indexes = api.get_indexes()
    # print(indexes)
    # artists = api.get_artists()
    # print(artists)
    # artist = api.get_artist(artists[0].artists[0].id)
    # print(artist)
    # album_songs = api.get_album(artist.albums[0].id)
    # print(album_songs, artist.albums[0].song_count)
    # music_directory = api.get_music_directory('6')
    # print(music_directory)
    #
    # all_albums = api.get_album_list(ListTypes.ALPHABETICAL_ARTIST)
    # print(all_albums)

    # songs = list(api.get_all_songs_fast())
    # print('len of songs', len(songs))
    t = Timer(lambda: list(api.get_all_songs_fast()))
    fast_s = t.timeit(number=1)
    print('fast', fast_s)

    t = Timer(api.get_all_songs)
    api_s = t.timeit(number=1)
    print('api only', api_s)


    # stream_url = api.private_stream_url(songs[3].id)
    # print(stream_url)
    # # print(api.start_scan())
    # print(api.get_scan_status())
    # share_collection = api.create_share('15')
    # print(share_collection)
    # wild_search = api.search_query('linkin park')
