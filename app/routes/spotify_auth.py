from flask import Blueprint, redirect, request, jsonify, url_for, make_response
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timedelta
import urllib.parse
from urllib.parse import urlencode
import os
import requests
from models.user import User
from models.temp import TemporaryStorage  
from app import db
from flask_cors import cross_origin
import base64
import hashlib

# Spotify API endpoints and credentials
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')

spotify_auth_routes = Blueprint('spotify_auth_routes', __name__)

def generate_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).rstrip(b'=').decode('utf-8')
    return code_verifier, code_challenge

def generate_unique_session_id():
    return base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')

@spotify_auth_routes.route('/login', methods=['GET'])
@cross_origin(supports_credentials=True, origins='*')
def login():
    code_verifier, code_challenge = generate_code_verifier_and_challenge()
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': 'https://be-spotify-weather.onrender.com/callback',
        'scope': SPOTIFY_SCOPES,
        'code_challenge_method': 'S256',
        'code_challenge': code_challenge,
        'show_dialog': 'true'
    }
    auth_url = f'{AUTH_URL}?{urllib.parse.urlencode(params)}'
    session_id = generate_unique_session_id()
    
    # Calculate the expiration time (e.g., 1 hour from now)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    temp_storage = TemporaryStorage(key=session_id, value=code_verifier, expires_at=expires_at)
    db.session.add(temp_storage)
    db.session.commit()
    
    response = make_response(jsonify({'auth_url': auth_url, 'session_id': session_id}))
    response.set_cookie('session_id', value=session_id, secure=False, httponly=False, samesite='Lax')
    
    
    return response

@spotify_auth_routes.route('/close')
def close_popup():
    return '''<html><body>
              <script>
              window.opener.postMessage('loginSuccess', '*');
              window.close();
              </script>
              </body></html>'''

@spotify_auth_routes.route('/callback', methods=['GET'])
@cross_origin(supports_credentials=True, origins='*')
def callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "Authorization code not provided"}), 400

    session_id = request.cookies.get('session_id')
    print(session_id)
      # Assuming session_id is stored in cookies
    temp_storage = TemporaryStorage.query.filter_by(key=session_id).first()
    if not temp_storage:
        return jsonify({"error": "Session not found"}), 400
    code_verifier = temp_storage.value
    print("code_verifier: ", code_verifier)

    token_info = exchange_code_for_access_token(code, code_verifier)
    if 'access_token' not in token_info:
        return jsonify({"error": token_info.get('error', 'Failed to retrieve access token')}), 400

    access_token = token_info['access_token']
    user_id = fetch_user_id(access_token)
    if not user_id:
        return jsonify({"error": "Failed to retrieve user ID"}), 400

    user = update_or_create_user(user_id, token_info)
    if not user:
        return jsonify({"error": "Failed to update or create user"}), 500

    return prepare_response(access_token)

def exchange_code_for_access_token(code, code_verifier):
    print("inside exchange_code_for_access_token")
    req_body = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'https://be-spotify-weather.onrender.com/callback',
        'client_id': SPOTIFY_CLIENT_ID,
        'code_verifier': code_verifier
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(TOKEN_URL, data=urlencode(req_body), headers=headers)
    print(response.json())
    return response.json()

def fetch_user_id(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(API_BASE_URL + 'me', headers=headers)
    return response.json().get('id')

def update_or_create_user(user_id, token_info):
    expires_at = datetime.now() + timedelta(seconds=token_info['expires_in'])
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        user.access_token = token_info['access_token']
        user.refresh_token = token_info.get('refresh_token')  # Some flows might not return a new refresh token
        user.expires_at = expires_at
    else:
        user = User(
            user_id=user_id,
            access_token=token_info['access_token'],
            refresh_token=token_info['refresh_token'],
            expires_at=expires_at
        )
        db.session.add(user)
    db.session.commit()
    return user

def prepare_response(access_token):
    response = make_response(redirect(url_for('spotify_auth_routes.close_popup')))
    response.set_cookie('accessToken', value=access_token, secure=False, httponly=False, samesite='Lax')  
    return response

# Helper function to get the user from the access token
def get_user_from_token(access_token):
    if access_token:
        # Use the helper function to query the user by access token
        user = User.query.filter_by(access_token=access_token).one()
        expires_at_datetime = datetime.strptime(user.expires_at, '%Y-%m-%d %H:%M:%S.%f')
        if user and datetime.now().timestamp() < expires_at_datetime.timestamp():
            return user.json()
        else:
            # Redirect to token refresh if the token has expired or no user is found
            return redirect(url_for('spotify_auth_routes.refresh_token'))
        
