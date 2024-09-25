import json

from openai import OpenAI
import streamlit as st

from spotify_controller import SpotifyController


def read_secrets():
    with open('secrets.json', 'r') as file:
        return json.load(file)


class Menu:
    def __init__(self):
        # read secrets.json
        self.secrets = read_secrets()

        spotify_scopes = ("user-library-read,user-read-recently-played,user-read-playback-state,"
                          "user-modify-playback-state,playlist-modify-public,playlist-modify-private")
        self.sp = SpotifyController(credentials=self.secrets, scopes=spotify_scopes)
        self.draw_page()

    def draw_page(self):
        openai_key = self.secrets['openai']['key']
        with st.sidebar:
            openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password", value=openai_key)

            if openai_api_key is not None:
                if st.button('clear chat'):
                    st.session_state.clear()

        st.title("Spotify api chatbot")
        st.caption("A gpt-4o-mini chatbot that interacts with your Spotify account.")
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input():
            if not openai_api_key:
                st.info("Please add your OpenAI API key to continue.")
                st.stop()

            client = OpenAI(api_key=openai_api_key)
            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })
            st.chat_message("user").write(prompt)

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
                                       "playing something,"
                                       "for example when user says 'pause'"
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
                        "name": "add_to_queue",
                        "description": "Add tracks to a playing queue. For example, when user says 'add to queue "
                                       "track1 and track2', you should call this function with parameter ['track1', "
                                       "'track2']",
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
                        "name": "switch_to_next_track",
                        "description": "Switch current playback to a next track. For example, when users says 'play "
                                       "next track', you should call this function",

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
                                       "playlist that contains the tracks based on user\'s description",
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
            ]

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                tools=tools
            )
            msg = response.choices[0].message.content

            tool_call = response.choices[0].message.tool_calls
            if tool_call is not None:

                called_function = tool_call[0].function.name

                functions = {
                    'play_track': self.sp.play_track,
                    'pause_playback': self.sp.pause_playback,
                    'resume_playback': self.sp.resume_playback,
                    'add_to_queue': self.sp.add_to_queue,
                    'switch_to_next_track': self.sp.switch_to_next_track,
                    'switch_to_previous_track': self.sp.switch_to_previous_track,
                    'get_my_current_playback': self.sp.get_my_current_playback,
                    'create_playlist_with_tracks': self.sp.create_playlist_with_tracks
                }

                if called_function in functions:
                    arguments = json.loads(tool_call[0].function.arguments)
                    msg = functions[called_function](**arguments)


            msg = ' ' if msg is None else msg  # in case msg is None it won't crash streamlit

            st.session_state.messages.append({
                "role": "assistant",
                "content": msg
            })

            st.chat_message("assistant").write(msg)
