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
            print(f"Error initializing SpotifyController: {e}")

    def _get_current_playback(self):
        return self.sp.current_playback()

    def _create_playlist(self, name: str):
        return self.sp.user_playlist_create(self.sp.me()['id'], name)

    def play_track(self, track_uri=None, track_name=None):
        if track_uri:
            self.sp.start_playback(uris=[track_uri])
        if track_name:
            track = self.search_track(track_name)
            self.sp.start_playback(uris=[track])
        else:
            return None
        return f'Playing {track_name}...'

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

    def search_track(self, query: str):
        return self.sp.search(query, limit=1)['tracks']['items'][0]['uri']

    def add_to_queue(self, tracks_to_search):
        for track in tracks_to_search:
            searched_track = self.search_track(track)
            if searched_track is not None:
                self.sp.add_to_queue(searched_track)
            else:
                print(f'could not play {searched_track}')

        return f'added {", ".join(tracks_to_search)} to a queue'

    def switch_to_next_track(self):
        self.sp.next_track()

        return f'Skipping {self._get_current_playback()["item"]["name"]}'

    def switch_to_previous_track(self):
        self.sp.previous_track()

        return f'Switching to previous track...'

    def get_my_current_playback(self):
        current_playback = self._get_current_playback()

        if current_playback is not None:
            track_name = current_playback["item"]["name"]
            artist_name = current_playback["item"]["artists"][0]["name"]
            msg = f'Currently playing: {track_name} by {artist_name}'
            return msg
        else:
            return 'No track is currently playing'

    def create_playlist_with_tracks(self, name: str, tracks: list):
        playlist = self._create_playlist(name)
        track_ids = [self.search_track(track) for track in tracks]

        self.sp.playlist_add_items(playlist['id'], track_ids)

        return f'Here\'s your generated playlist: {playlist['external_urls']['spotify']}'
