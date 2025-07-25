<<<<<<< HEAD
import requests
import os
from dotenv import load_dotenv

env_loaded = load_dotenv()
print("ENV loaded:", env_loaded)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

print(f'cred: {CLIENT_ID} , {CLIENT_SECRET}')
def get_spotify_token():
    auth_response = requests.post(
        'https://accounts.spotify.com/api/token',
        data={'grant_type': 'client_credentials'},
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    print(f"Response of Spotify: {auth_response.json()}")
    return auth_response.json()['access_token']

def get_song_by_emotion(emotion: str):
    token = get_spotify_token()
    headers = {'Authorization': f'Bearer {token}'}
    search_url = f"https://api.spotify.com/v1/search?q={emotion}&type=playlist&limit=1"
    res = requests.get(search_url, headers=headers)
    data = res.json()
    playlist = data['playlists']['items'][0]
    
    playlist_id = playlist['id']
    
    tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    tracks_res = requests.get(tracks_url, headers=headers)
    tracks_data = tracks_res.json()

    songs = []
    for item in tracks_data['items']:
        track = item['track']
        song_name = track['name']
        artists = ", ".join(artist['name'] for artist in track['artists'])
        songs.append(f"{song_name} by {artists}")

    return {
        'emotion': emotion,
        'playlist_url': playlist['external_urls']['spotify'],
        'songs': songs
=======
import requests
import os
from dotenv import load_dotenv

env_loaded = load_dotenv()
print("ENV loaded:", env_loaded)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

print(f'cred: {CLIENT_ID} , {CLIENT_SECRET}')
def get_spotify_token():
    auth_response = requests.post(
        'https://accounts.spotify.com/api/token',
        data={'grant_type': 'client_credentials'},
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    print(f"Response of Spotify: {auth_response.json()}")
    return auth_response.json()['access_token']

def get_song_by_emotion(emotion: str):
    token = get_spotify_token()
    headers = {'Authorization': f'Bearer {token}'}
    search_url = f"https://api.spotify.com/v1/search?q={emotion}&type=playlist&limit=1"
    res = requests.get(search_url, headers=headers)
    data = res.json()
    playlist = data['playlists']['items'][0]
    
    playlist_id = playlist['id']
    
    tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    tracks_res = requests.get(tracks_url, headers=headers)
    tracks_data = tracks_res.json()

    songs = []
    for item in tracks_data['items']:
        track = item['track']
        song_name = track['name']
        artists = ", ".join(artist['name'] for artist in track['artists'])
        songs.append(f"{song_name} by {artists}")

    return {
        'emotion': emotion,
        'playlist_url': playlist['external_urls']['spotify'],
        'songs': songs
>>>>>>> db2d7506b05bc40d8aca21622d9cb938ce61cd04
    }