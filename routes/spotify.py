from flask import Blueprint, redirect, request, jsonify, url_for
import os
import logging
import urllib.parse
import datetime
import requests


logging.basicConfig(level=logging.INFO)

# Spotify API endpoints
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

# Get Spotify API keys
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')
EXPIRES_AT = os.getenv('EXPIRES_AT')
USER_ID = os.getenv('USER_ID')

spotify_routes = Blueprint('spotify_routes', __name__)

# Handle login
@spotify_routes.route('/login', methods=['GET'])
def login():
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': SPOTIFY_SCOPES,
        'show_dialog': True
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return jsonify({'auth_url': auth_url})

# Handle if login is successful or not
@spotify_routes.route('/callback', methods=['POST'])
def callback():
    data = request.json
    if 'error' in data:
        return jsonify({"error": data['error']})
    
    if 'code' in data:
        req_body = {
            'code': data['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': SPOTIFY_REDIRECT_URI,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET
        }
        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        if 'access_token' in token_info:
            os.environ['ACCESS_TOKEN'] = str(token_info['access_token'])
            os.environ['REFRESH_TOKEN'] = str(token_info['refresh_token'])
            os.environ['EXPIRES_AT'] = str(datetime.datetime.now().timestamp() + token_info['expires_in'])


             # Get the user ID
            headers = {'Authorization': f'Bearer {token_info["access_token"]}'}
            response = requests.get(API_BASE_URL + 'me', headers=headers)
            os.environ['USER_ID'] = response.json()['id']

            return jsonify({"login_status": "successful"})
        else:
            return jsonify({"error": token_info.get('error', 'Failed to retrieve access token')})
    else:
        return jsonify({"error": "No code provided"})
    
# Helper function to check token
def get_access_token():
    # First, try to get the access token from the headers
    auth_header = request.headers.get('Authorization')
    if auth_header:
        return auth_header.split(' ')[1]

    # If the access token is not in the headers, fall back to the environment variables
    if ACCESS_TOKEN != str:
        return redirect(url_for('spotify_routes.login'))
    if datetime.datetime.now().timestamp() > float(os.environ['EXPIRES_AT']):
        return redirect(url_for('spotify_routes.refresh_token'))
    
    return ACCESS_TOKEN

#refresh token if our session expired
@spotify_routes.route('/refresh-token', methods=['GET'])
def refresh_token():
    if 'REFRESH_TOKEN' not in os.environ:
        return redirect(url_for('spotify_routes.login'))

    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': os.environ['REFRESH_TOKEN'],
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()

    os.environ['ACCESS_TOKEN'] = str(new_token_info['access_token'])
    os.environ['EXPIRES_AT'] = str(datetime.datetime.now().timestamp() + new_token_info['expires_in'])

    return redirect(url_for('weather_routes'))

#search for the top 50 playlist and return the song qualities of that list. 
@spotify_routes.route('/search', methods=['GET'])
def get_top_50_playlist():

    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country parameter is missing"}), 400

    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    params = {'q': f'top 50 {country}', 'type': 'playlist', 'limit': 1}
    response = requests.get(API_BASE_URL + 'search', headers=headers, params=params)
    print(f"ACCESS_TOKEN: {ACCESS_TOKEN}")  # Debug print
 
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch top 50 playlist from Spotify'}), response.status_code

    data = response.json()
    if not data['playlists']['items']: 
        return jsonify({'error': 'No playlist found'}), 404

    playlist_id = data['playlists']['items'][0]['id']
    return get_playlist_tracks(playlist_id)

def get_playlist_tracks(playlist_id):
        headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
        response = requests.get(f"{API_BASE_URL}playlists/{playlist_id}/tracks", headers=headers)
        logging.info(f'Spotify response: {response.status_code}, {response.text}')

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch tracks from Spotify"}), response.status_code

        data = response.json()
        track_ids = [item['track']['id'] for item in data['items']]
        logging.info(f'Track IDs: {track_ids}')

        return get_audio_features(track_ids)


def get_audio_features(track_ids):
        headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
        params = {'ids': ','.join(track_ids)}
        response = requests.get(f"{API_BASE_URL}audio-features", headers=headers, params=params)
        logging.info(f'Spotify response: {response.status_code}, {response.text}')

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch audio features from Spotify"}), response.status_code

        data = response.json()
        logging.info(f'Audio features: {data}')
        if 'audio_features' not in data:
            return jsonify({"error": "Failed to extract audio features from Spotify response"})

        return jsonify(data['audio_features'])
    
    # Create a new Spotify playlist
@spotify_routes.route('/create-playlist', methods=['POST'])
def create_playlist():
    data = request.json
    playlist_name = data.get('playlist_name')
    access_token = get_access_token()

    response = requests.post(
        f"{API_BASE_URL}users/{USER_ID}/playlists",
        headers={'Authorization': f'Bearer {access_token}'},
        json={'name': playlist_name, 'description': 'Generated by WeatherTunes', 'public': False}
    )
    if response.status_code != 201:
        return jsonify({"error": "Failed to create playlist"}), response.status_code

    playlist_id = response.json()['id']
    return jsonify({'playlist_id': playlist_id, 'playlist_name': playlist_name})

# Add tracks to a Spotify playlist
@spotify_routes.route('/add-tracks', methods=['POST'])
def add_tracks_to_playlist():
    data = request.json
    playlist_id = data.get('playlist_id')
    track_uris = data.get('track_uris')
    playlist_url = data.get('playlist_url')
    access_token = get_access_token()

    response = requests.post(
        f"{API_BASE_URL}playlists/{playlist_id}/tracks",
        headers={'Authorization': f'Bearer {access_token}'},
        json={'uris': track_uris}
    )
    if response.status_code != 201:
        return jsonify({"error": "Failed to add tracks to playlist"}), response.status_code

    return jsonify({'success': True, 'playlist_id': playlist_id})