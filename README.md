# Spotbot

A streamlit web application that integrates gpt-4o-mini model to allow user control their Spotify account (features such as controlling playback, adding tracks to queue, creating playlist based on description) through a natural language assistant.


## Installation

```bash
  git clone https://github.com/Spacoon/spotbot
  pip install streamlit
  pip install spotipy --upgrade
  pip install openai
```
Also, you will need to enter your [Spotify's Client ID, Client Secret, Redirect URI](https://developer.spotify.com/documentation/web-api/concepts/apps) and [OpenAi's api key](https://platform.openai.com/docs/quickstart/create-and-export-an-api-key) into secrets.json.

## Running

Run as a shell script
```bash 
streamlit run <your/path/to/main.py>
```
