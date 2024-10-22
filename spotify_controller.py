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

            self.sp.add_to_queue(track)
            self.sp.next_track()

            # sp.start_playback plays the given track, but unfortunately erases a queue, so it's better to use
            # add_to_queue and next_track
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

    def get_my_current_playback(self):
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

    def get_my_top_tracks(self, tracks=50):
        top_tracks = self._fetch_top_tracks(tracks)
        top_tracks_names = [track['name'] for track in top_tracks]
        top_tracks_artists = [track['artists'][0]['name'] for track in top_tracks]

        for i in range(len(top_tracks_names)):
            top_tracks_names[i] += f' by {top_tracks_artists[i]}'

        return Response(listed_tracks=top_tracks_names)

    def get_my_top_artists(self, tracks=50):
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


class OpenAiTools:
    tools = [
        {
            "type": "function",
            "function": {
                "name": "play_track",
                "description": "Play a song. Call this whenever you are asked to play something, "
                               "for example when user says 'play a song'",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "track_name": {
                            "type": "string",
                            "description": "Title of a track to play"
                        },
                    },
                    "required": ["track_name"],
                    "additionalProperties": False,
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "pause_playback",
                "description": "Pause playback of a track. Call this whenever you are asked to stop or pause "
                               "playing something, for example when user says 'pause'"
            }
        },
        {
            "type": "function",
            "function": {
                "name": "resume_playback",
                "description": "Resume playback of a track. Call this whenever you are asked to resume or "
                               "start playing something (but if user asks you to play a certain song, "
                               "you should not call this function), for example when user says 'play'",
            }
        },
        {
            "type": "function",
            "function": {
                "name": "switch_to_next_track",
                "description": "Switch current playback to a next track. For example, when users says 'play next "
                               "track', you should call this function.",
            }
        },
        {
            "type": "function",
            "function": {
                "name": "switch_to_previous_track",
                "description": "Switch current playback to a previous track. For example, when users says 'play"
                               " previous track', you should call this function",

            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_to_queue",
                "description": "Add tracks to a playing queue. For example, when user says 'add to queue track1 and "
                               "track2', you should call this function with parameter ['track1', 'track2']",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tracks": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Titles of tracks, each and every one put in a list"
                        },
                    },
                    "required": ["tracks"],
                    "additionalProperties": False,
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_my_current_playback",
                "description": "Get the current playback. For example, when users says 'what is playing', "
                               "you should call this function",
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_playlist_with_tracks",
                "description": "Create a playlist with tracks. Call this function when you want to create a "
                               "playlist that contains the tracks based on user\'s description.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tracks": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Titles of tracks based on user\'s response."
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the playlist. If not provided, come up with a name yourself"
                        }
                    },
                    "required": ["tracks", "name"],
                    "additionalProperties": False,
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_my_top_tracks",
                "description": "Get user\'s favorite tracks. Call this function when you want to get user\'s top tracks",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tracks": {
                            "type": "integer",
                            "description": "Number of top tracks to get"
                        }
                    },
                    "required": ["tracks"],
                    "additionalProperties": False,
                },
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_my_top_artists",
                "description": "Get user\'s favorite artists. Call this function when you want to get user\'s top "
                               "artists, performers, or bands",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tracks": {
                            "type": "integer",
                            "description": "Number of top artists to get"
                        }
                    },
                    "required": ["tracks"],
                    "additionalProperties": False,
                },
            }
        },
    ]
