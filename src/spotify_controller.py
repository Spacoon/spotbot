import json
from pprint import pprint
from time import sleep

import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyController:
    def __init__(self, credentials: json, scopes: str):
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scopes,
                                                                client_id=credentials['spotify']['client_id'],
                                                                client_secret=credentials['spotify'][
                                                                    'client_secret'],
                                                                redirect_uri=credentials['spotify'][
                                                                    'redirect_uri']))
        except Exception as e:
            print(f"Error initializing SpotifyController: \n{e}")



    def _get_current_playback(self):
        return self.sp.current_playback()

    def _create_playlist(self, name: str):
        return self.sp.user_playlist_create(self.sp.me()['id'], name)

    def get_user_profile_name(self):
        user = self.sp.me()
        return user['display_name'], user['external_urls']['spotify'], user['images'][0]['url']

    def _fetch_top_tracks(self, tracks=50):
        iterations = tracks // 50
        last_iteration = tracks % 50

        top_tracks = []

        for i in range(iterations):
            top_tracks += self.sp.current_user_top_tracks(limit=50, offset=i * 50, time_range='long_term')['items']

        if last_iteration:
            top_tracks += self.sp.current_user_top_tracks(limit=last_iteration, offset=iterations * 50,
                                                          time_range='long_term')['items']

        return top_tracks

    def _fetch_top_artists(self, artists=50):
        iterations = artists // 50
        last_iteration = artists % 50

        top_artists = []

        for i in range(iterations):
            top_artists += self.sp.current_user_top_artists(limit=50, offset=i * 50, time_range='long_term')['items']

        if last_iteration:
            top_artists += self.sp.current_user_top_artists(limit=last_iteration, offset=iterations * 50,
                                                            time_range='long_term')['items']

        return top_artists

    def _search_track(self, query: str, limit=1):
        return self.sp.search(query, limit=limit)

    def is_device_active(self):
        for device in self.sp.devices()['devices']:
            if device['is_active']:
                return True
        return False

    def play_track(self, track_name=None):
        if track_name:
            track = self._search_track(track_name)['tracks']['items'][0]['uri']

            self.sp.add_to_queue(track)
            self.sp.next_track()

            # self.sp.start_playback(uris=[track])
            # sp.start_playback plays the given track, but unfortunately erases a queue, so it's better to use
            # add_to_queue and next_track
        else:
            return None
        return track_name

    def pause_playback(self):
        if self.sp.current_playback()['is_playing']:
            self.sp.pause_playback()
            return 'Stopped playback'
        else:
            return 'Playback is already paused'

    def resume_playback(self):
        if not self.sp.current_playback()['is_playing']:
            self.sp.start_playback()
            return 'Resumed playback'
        else:
            return 'Playback is already playing'

    def add_to_queue(self, tracks):
        searched_track_names = ''
        for track in tracks:
            searched_track = self._search_track(track)['tracks']['items'][0]
            # pprint(searched_track)
            if searched_track is not None:
                # pprint(searched_track)
                self.sp.add_to_queue(searched_track['uri'])
                searched_track_names += f'{searched_track['name']} by {searched_track["artists"][0]["name"]}, '
                # pprint(searched_track_names)
            else:
                print(f'could not play {searched_track}')

        return ", ".join(searched_track_names)

    def switch_to_next_track(self):
        self.sp.next_track()
        sleep(0.1)
        playback = self._get_current_playback()["item"]

        return f'{playback["name"]} by {playback["artists"][0]["name"]}'

    def switch_to_previous_track(self):
        self.sp.previous_track()
        sleep(0.1)
        playback = self._get_current_playback()["item"]

        return f'{playback["name"]} by {playback["artists"][0]["name"]}'

    def get_user_current_playback(self):
        current_playback = self._get_current_playback()

        if current_playback is not None:
            track_name = current_playback["item"]["name"]
            artist_name = current_playback["item"]["artists"][0]["name"]
            return f'{track_name} + by {artist_name}'
        else:
            return 'No track is currently playing'

    def create_playlist_with_tracks(self, name: str, tracks: list):
        playlist = self._create_playlist(name)
        track_ids = [self._search_track(track) for track in tracks]

        self.sp.playlist_add_items(playlist['id'], track_ids)

        return playlist['external_urls']['spotify']

    def get_user_top_tracks(self, tracks=50):
        top_tracks = self._fetch_top_tracks(tracks)
        top_tracks_names = [track['name'] for track in top_tracks]
        top_tracks_artists = [track['artists'][0]['name'] for track in top_tracks]

        for i in range(len(top_tracks_names)):
            top_tracks_names[i] += f' by {top_tracks_artists[i]}'

        return ", ".join(top_tracks_names)

    def get_user_top_artists(self, tracks=50):
        top_artists = self._fetch_top_artists(tracks)
        top_artists_names = [artist['name'] for artist in top_artists]

        return ", ".join(top_artists_names)
