import requests
from urllib.parse import urlencode
import os

SPOTIFY_API_URL = 'https://accounts.spotify.com'
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')

def get_spotify_auth_url():
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': SPOTIFY_SCOPES
    }
    auth_url = f'{SPOTIFY_API_URL}/authorize?{urlencode(params)}'
    return auth_url

def get_spotify_tokens(code):
    data = {
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI
    }
    response = requests.post(f'{SPOTIFY_API_URL}/api/token', data=data)
    tokens = response.json()
    return tokens