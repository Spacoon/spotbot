# Spotbot

A web application that integrates OpenAi’s GPT-4o-mini model with Spotify API to enable AI-powered music control and playlist curation. The application allows users to control their Spotify playback and manage their queue. Implemented a creative feature that leverages the OpenAI API to generate playlists based on user text descriptions, combining natural language processing with Spotify's service.

## Installation

```bash
  git clone https://github.com/Spacoon/spotbot
  cd spotbot
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
```
Also, you need to enter your [Spotify's Client ID, Client Secret, Redirect URI](https://developer.spotify.com/documentation/web-api/concepts/apps) and [OpenAi's api key](https://platform.openai.com/docs/quickstart/create-and-export-an-api-key) into secrets.json.

## Running

Run as a shell script
```bash 
streamlit run src/main.py
# or streamlit run <your/path/to/main.py>
```

![alt text](https://github.com/Spacoon/spotbot/blob/main/showcase.jpg)
