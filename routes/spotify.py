from flask import Blueprint, redirect, request, jsonify, session
from flask_session import Session
import os
import logging
import urllib.parse
import datetime
import requests


logging.basicConfig(level=logging.DEBUG)

# Spotify API endpoints
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'  # Correct the version here

# Get Spotify API keys
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')


spotify_routes = Blueprint('spotify_routes', __name__)

#handle login
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
    return redirect(auth_url)

#handle if login is successful or not
@spotify_routes.route('/callback', methods=['GET'])
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': SPOTIFY_REDIRECT_URI,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.datetime.now().timestamp() + token_info['expires_in']

        return redirect('/playlists')
    else:
        return jsonify({"error": "No code provided"})
#helper function, check if we have a token, need to refresh or need to login    
def get_access_token():
    if 'access_token' not in session:
        return redirect('login')
    if datetime.datetime.now().timestamp() > session ['expires_at']:
        return redirect ('/refresh-token')
    return session['access_token']

@spotify_routes.route('/search', methods=['GET'])
def get_top_50_playlist():
    country = request.args.get('country')
    if not country:
        return jsonify({"error": "Country parameter is missing"}), 400

    if 'access_token' not in session:
        return redirect('/login')

    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    access_token = session['access_token']

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    params = {
        'q': f'top 50 {country}',
        'type': 'playlist',
        'limit': 1
    }

    response = requests.get(API_BASE_URL + 'search', headers=headers, params=params)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch playlists from Spotify"}), response.status_code

    data = response.json()
    if not data['playlists']['items']:
        return jsonify({"error": "No playlist found"}), 404

    playlist_id = data['playlists']['items'][0]['id']
    
    # You can save the playlist ID in session or database as needed
    session['playlist_id'] = playlist_id

    return jsonify({"playlist_id": playlist_id})


@spotify_routes.route('/playlists', methods=['GET'])
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')

    access_token = session['access_token']

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()

    return jsonify(playlists)


@spotify_routes.route('/refresh-token', methods=['GET'])
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/playlists')

