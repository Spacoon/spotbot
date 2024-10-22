import json

from openai import OpenAI

import streamlit as st


from spotify_controller import SpotifyController, OpenAiTools


def read_secrets():
    with open('secrets.json', 'r') as file:
        return json.load(file)


class Menu:
    def __init__(self):
        self.secrets = read_secrets()

        self.sp = SpotifyController(credentials=self.secrets, scopes="user-library-read,"
                                                                     "user-read-recently-played,"
                                                                     "user-read-playback-state,"
                                                                     "user-modify-playback-state,"
                                                                     "playlist-modify-public,"
                                                                     "playlist-modify-private,"
                                                                     "user-top-read")

        if not self.sp.is_device_active():
            st.error("You don't have any active devices. Please open Spotify on your device and refresh the page.")
            st.stop()


        self.username = self.sp.get_user_profile_name()

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
            'get_my_current_playback': {
                'func': self.sp.get_my_current_playback,
                'message': lambda message: f'Currently playing: {message}'
            },
            'create_playlist_with_tracks': {
                'func': self.sp.create_playlist_with_tracks,
                'message': lambda message: f'Here\'s your playlist: {message}'
            },
            'get_my_top_tracks': {
                'func': self.sp.get_my_top_tracks,
                'message': lambda message: f'Here are your top tracks of all time:\n\n{message}'
            },
            'get_my_top_artists': {
                'func': self.sp.get_my_top_artists,
                'message': lambda message: f'Here are your top artists of all time:\n\n{message}'
            },
        }

        self.draw_page()

    def draw_page(self):
        st.set_page_config(page_title="Spotify Chatbot", page_icon="🎵", layout="wide")

        openai_key = self.secrets['openai']['key']
        with st.sidebar:
            self.handle_sidebar()

        st.title("Spotify api chatbot")
        st.caption("A gpt-4o-mini chatbot that interacts with your Spotify account\n\n"
                   "(please note that it's not affiliated in any way with Spotify company).")



        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input():
            if not openai_key:
                st.info("Please add your OpenAI API key to continue.")
                st.stop()

            client = OpenAI(api_key=openai_key)
            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })
            st.chat_message("user").write(prompt)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                tools=OpenAiTools.tools
            )
            msg = response.choices[0].message.content

            tool_call = response.choices[0].message.tool_calls
            if tool_call is not None:
                called_function = tool_call[0].function.name

                if called_function in self.function_map:
                    arguments = json.loads(tool_call[0].function.arguments)
                    func = self.function_map[called_function]['func']
                    message_func = self.function_map[called_function]['message']

                    result = func(**arguments)
                    msg = message_func(result)

            msg = ' ' if msg is None else msg  # in case msg is None it won't crash streamlit

            st.session_state.messages.append({
                "role": "assistant",
                "content": msg
            })

            st.chat_message("assistant").write(msg)

    def handle_sidebar(self):
        st.image(self.username[2], use_column_width=True)
        st.write(f"Logged in as: [{self.username[0]}]({self.username[1]})")
        st.sidebar.title("Menu")
        if st.button('clear chat'):
            st.session_state.clear()
        st.sidebar.write(self.function_map.keys())
