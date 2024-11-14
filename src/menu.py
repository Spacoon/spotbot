import json

from openai import OpenAI
import streamlit as st
# from rich.pretty import pprint

from spotify_controller import SpotifyController


def _read_secrets():
    with open('secrets.json', 'r') as file:
        return json.load(file)


class Menu:
    def __init__(self):
        self.secrets = _read_secrets()

        self.sp = SpotifyController(credentials=self.secrets, scopes="user-library-read,"
                                                                     "user-read-recently-played,"
                                                                     "user-read-playback-state,"
                                                                     "user-modify-playback-state,"
                                                                     "playlist-modify-public,"
                                                                     "playlist-modify-private,"
                                                                     "user-top-read"
                                    )

        # if user doesn't have any active devices, it will stop the app
        if not self.sp.is_device_active():
            st.error("You don't have any active devices. Please open Spotify on your device and refresh the page.")
            st.stop()

        self.username = self.sp.get_user_profile_name()

        self.client = OpenAI(api_key=self.secrets['openai']['key'])

        self.function_map = {
            'play_track': {
                'func': self.sp.play_track,
                'message': lambda message: f'Playing {message}'
            },
            'pause_playback': {
                'func': self.sp.pause_playback,
                'message': lambda message: 'Stopped playback'
            },
            'resume_playback': {
                'func': self.sp.resume_playback,
                'message': lambda message: 'Resumed playback'
            },
            'add_to_queue': {
                'func': self.sp.add_to_queue,
                'message': lambda message: f'Added {message} to a queue'
            },
            'switch_to_next_track': {
                'func': self.sp.switch_to_next_track,
                'message': lambda message: f'Skipping {message}'
            },
            'switch_to_previous_track': {
                'func': self.sp.switch_to_previous_track,
                'message': lambda message: f'Switching to previous track...'
            },
            'get_user_current_playback': {
                'func': self.sp.get_user_current_playback,
                'message': lambda message: f'Currently playing: {message}'
            },
            'create_playlist_with_tracks': {
                'func': self.sp.create_playlist_with_tracks,
                'message': lambda message: f'Here\'s your playlist: {message}'
            },
            'get_user_top_tracks': {
                'func': self.sp.get_user_top_tracks,
                'message': lambda message: f'Here are your top tracks of all time:\n\n{message}'
            },
            'get_user_top_artists': {
                'func': self.sp.get_user_top_artists,
                'message': lambda message: f'Here are your top artists of all time:\n\n{message}'
            },
        }

        self.tools = [
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
                    "name": "get_user_current_playback",
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
                    "name": "get_user_top_tracks",
                    "description": "Get user\'s favorite tracks. Call this function when you want to get user\'s top "
                                   "tracks",
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
                    "name": "get_user_top_artists",
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


        self.message = ''
        self.func_map = {}

        self._draw_page()

    def _draw_page(self):
        st.set_page_config(page_title="Spotify Chatbot", page_icon="🎵", layout="wide")

        openai_key = self.secrets['openai']['key']
        with st.sidebar:
            self._handle_sidebar()

        st.title("Spotify api chatbot")
        st.caption("A gpt-4o-mini chatbot that interacts with your Spotify account\n\n"
                   "(please note that it's not affiliated in any way with Spotify company).")

        self._handle_chat(openai_key)

    def _handle_sidebar(self):
        st.image(self.username[2], use_column_width=True)
        st.write(f"Logged in as: [{self.username[0]}]({self.username[1]})")

        st.sidebar.title("Menu")
        if st.button('clear chat'):
            st.session_state.clear()

    def _handle_tool_call(self, tool_call):
        called_tools_descriptions = []
        called_tools_arguments = []
        details = []

        for item in tool_call.items():
            # pprint(item)

            arguments = json.loads(item[1]['args'])
            function = item[1]['name']


            for tool in self.tools:
                if tool['function']['name'] == function:
                    called_tools_descriptions.append(tool['function']['description'])

            if arguments:
                called_tools_arguments.append(str(arguments))


            func = self.function_map[function]['func']
            message_func = self.function_map[function]['message']

            result = func(**arguments)

            if result:
                details.append(str(result))
            # msg = message_func(result)

        # pprint(called_tools_descriptions)
        # pprint(called_tools_arguments)
        # pprint(details)

        stream = self._create_response_to_tool(called_tools_descriptions, called_tools_arguments, details)

        for chunk in stream:
            yield chunk


    def _handle_chat(self, openai_key):
        if "messages" not in st.session_state:
            st.session_state["messages"] = [
                {
                    "role": "assistant",
                    "content": "How can I help you?"
                }
            ]

        for msg in st.session_state.messages:
            st.chat_message(
                msg["role"]).write(
                msg["content"]
            )

        if prompt := st.chat_input():
            if not openai_key:
                st.info("Please add your OpenAI API key to continue.")
                st.stop()


            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })
            st.chat_message("user").write(prompt)

            self.stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                tools=self.tools,
                stream=True
            )

            st.chat_message("assistant").write_stream(self._stream_messages)


            st.session_state.messages.append({
                "role": "assistant",
                "content": self.message
            })

    def _stream_messages(self):
        current_key = -1
        for chunk in self.stream:
            # if it's a normal message, not a tool call
            if chunk.choices[0].delta.content is not None:
                self.message += chunk.choices[0].delta.content
                yield chunk.choices[0].delta.content

            # if it's a tool call(s)
            if chunk.choices[0].delta.tool_calls is not None:
                # if there are multiple tool calls, it will group them by their index (current_key)
                if chunk.choices[0].delta.tool_calls[0].index != current_key:
                    current_key = chunk.choices[0].delta.tool_calls[0].index
                    self.func_map[current_key] = {
                        "name": chunk.choices[0].delta.tool_calls[0].function.name,
                        "args": ""
                    }
                self.func_map[current_key]["args"] += chunk.choices[0].delta.tool_calls[0].function.arguments


        # if there are any tool calls, it will call the function(s) and return the response
        if self.func_map:
            # pprint(self.func_map)

            msg = self._handle_tool_call(self.func_map)
            for chunk in msg:
                self.message += chunk
                yield chunk


    def _create_response_to_tool(self, called_tools_descriptions: list, called_tools_arguments: list, details: list):
        prompt = (f'Function(s) called: {", ".join(called_tools_descriptions)}\n\n'
                  f'Arguments passed: {", ".join(called_tools_arguments)}\n\n'
                  f'Details: {", ".join(details)}')

        messages = [
            {
                "role": "system",
                "content": "You are a chatbot that interacts with Spotify API. You are given a task to create a "
                           "response to a tool call. Based on description of the tool call and its arguments, "
                           "you should create a unique response that will be returned to the user."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            stream=True
        )

        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
