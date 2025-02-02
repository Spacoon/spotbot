
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyController:
    def __init__(self, credentials, scopes: str):
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

    def _search_track(self, query: str):
        return self.sp.search(query, limit=1)['tracks']['items'][0]['uri']

    def is_device_active(self):
        for device in self.sp.devices()['devices']:
            if device['is_active']:
                return True
        return False

    def play_track(self, track_uri=None, track_name=None):
        if track_uri:
            self.sp.add_to_queue(track_uri)
            self.sp.next_track()
            # self.sp.start_playback(uris=[track_uri])
        if track_name:
            track = self._search_track(track_name)

            # sp.start_playback plays the given track, but unfortunately erases a queue, so it's better to use
            # add_to_queue and next_track

            self.sp.add_to_queue(track)
            self.sp.next_track()

            # self.sp.start_playback(uris=[track])
        else:
            return None
        return Response(track_name)

    def pause_playback(self):
        if self.sp.current_playback()['is_playing']:
            self.sp.pause_playback()
            return Response('Stopped playback')
        else:
            return Response('Playback is already paused')

    def resume_playback(self):
        if not self.sp.current_playback()['is_playing']:
            self.sp.start_playback()
            return Response('Resumed playback')
        else:
            return Response('Playback is already playing')

    def add_to_queue(self, tracks):
        for track in tracks:
            searched_track = self._search_track(track)
            if searched_track is not None:
                self.sp.add_to_queue(searched_track)
            else:
                print(f'could not play {searched_track}')

        return Response(", ".join(tracks))

    def switch_to_next_track(self):
        self.sp.next_track()

        return Response(self._get_current_playback()["item"]["name"])

    def switch_to_previous_track(self):
        self.sp.previous_track()
        return Response('Switching to previous track...')

    def get_user_current_playback(self):
        current_playback = self._get_current_playback()

        if current_playback is not None:
            track_name = current_playback["item"]["name"]
            artist_name = current_playback["item"]["artists"][0]["name"]
            return Response(track_name + f' by {artist_name}')
        else:
            return Response('No track is currently playing')

    def create_playlist_with_tracks(self, name: str, tracks: list):
        playlist = self._create_playlist(name)
        track_ids = [self._search_track(track) for track in tracks]

        self.sp.playlist_add_items(playlist['id'], track_ids)

        return Response(playlist['external_urls']['spotify'])

    def get_user_top_tracks(self, tracks=50):
        top_tracks = self._fetch_top_tracks(tracks)
        top_tracks_names = [track['name'] for track in top_tracks]
        top_tracks_artists = [track['artists'][0]['name'] for track in top_tracks]

        for i in range(len(top_tracks_names)):
            top_tracks_names[i] += f' by {top_tracks_artists[i]}'

        return Response(listed_tracks=top_tracks_names)

    def get_user_top_artists(self, tracks=50):
        top_artists = self._fetch_top_artists(tracks)
        top_artists_names = [artist['name'] for artist in top_artists]

        return Response(listed_tracks=top_artists_names)


class Response:
    message_details: str
    listed_tracks: str

    def __init__(self, details='', listed_tracks=None):
        self.message_details = details

        if listed_tracks:
            self.listed_tracks = "\n\n".join(listed_tracks)

    def __str__(self):
        if self.message_details:
            return self.message_details
        elif self.listed_tracks:
            return self.listed_tracks
        else:
            return ''
