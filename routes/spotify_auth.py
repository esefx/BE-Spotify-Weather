from flask import Blueprint, redirect, request, jsonify, url_for, make_response
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
import urllib.parse
import os
import requests
from models.user import User
from app import db
from flask_cors import cross_origin

# Spotify API endpoints
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token?'
API_BASE_URL = 'https://api.spotify.com/v1/'

# Get Spotify API keys
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')


spotify_auth_routes = Blueprint('spotify_auth_routes', __name__)

# Handle login
@spotify_auth_routes.route('/login', methods=['GET'])
def login():
    params = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': SPOTIFY_SCOPES,
        'show_dialog': True
    }
    auth_url = f'{AUTH_URL}?{urllib.parse.urlencode(params)}'
    return jsonify({'auth_url': auth_url})

@spotify_auth_routes.route('/close')
def close_popup():
    return '''<html><body>
              <script>
              window.opener.postMessage('loginSuccess', '*');
              window.close();
              </script>
              </body></html>'''

@spotify_auth_routes.route('/callback', methods=['GET'])
@cross_origin(supports_credentials=True, origins='http://localhost:3000')  # Adjust the origins as per your frontend's URL

def callback():
    print("start of callback")
    code = request.args.get('code')
    print("Authorization code:", code)

    if not code:
        return jsonify({"error": "Authorization code not provided"}), 400

    token_info = exchange_code_for_access_token(code)
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

def prepare_response(access_token):
    response = make_response(redirect(url_for('spotify_auth_routes.close_popup')))
    response.set_cookie('accessToken', value=access_token, secure=False, httponly=False, samesite='Lax')  
    return response

def exchange_code_for_access_token(code):
    req_body = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(TOKEN_URL, data=req_body)
    return response.json()

def fetch_user_id(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(API_BASE_URL + 'me', headers=headers)
    return response.json().get('id')

def update_or_create_user(user_id, token_info):
    expires_at = datetime.now().timestamp() + token_info['expires_in']
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        user.access_token = token_info['access_token']
        user.refresh_token = token_info['refresh_token']
        user.expires_at = datetime.fromtimestamp(expires_at)
    else:
        user = User(
            user_id=user_id,
            access_token=token_info['access_token'],
            refresh_token=token_info['refresh_token'],
            expires_at=datetime.fromtimestamp(expires_at)
        )
        db.session.add(user)
    db.session.commit()
    return user


#get access token from request cookies
def get_access_token():
    access_token = request.cookies.get('accessToken')
    if access_token:
        return access_token
    else:
        return {'error': 'Access token not found'}, 400
    
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

def update_access_token_in_db(user_id, new_access_token, new_expires_at):
    try:
        # Assuming user_identifier is an access token, adjust if it's a user ID or another identifier
        user = User.query.filter_by(user_id=user_id).one()
        user.access_token = new_access_token
        user.expires_at = new_expires_at
        db.session.commit()
    except NoResultFound:
        # Handle the case where no user is found, e.g., log an error or raise an exception
        pass

#refresh token if our session expired
@spotify_auth_routes.route('/refresh-token', methods=['GET'])
def refresh_token():
    access_token = get_access_token()

    if not access_token:
        # No access token provided, redirect to login
        return redirect(url_for('spotify_auth_routes.login'))

    #Identify the user by the access token
    user = get_user_from_token(access_token)
    if not user:
        # Access token does not match any user, redirect to login
        return redirect(url_for('spotify_auth_routes.login'))

    # Retrieve the user's refresh token from the database
    refresh_token = user.refresh_token
    if not refresh_token:
        # No refresh token found for the user, redirect to login
        return redirect(url_for('spotify_auth_routes.login'))

    # Request a new access token using the refresh token
    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()

    # Update the database with the new access token and its expiry
    update_access_token_in_db(user.user_id, new_token_info['access_token'], datetime.datetime.now().timestamp() + new_token_info['expires_in'])

    # return the new access token to the frontend
    response = make_response(redirect(url_for('your_redirect_route')))
    response.set_cookie('access_token', new_token_info['access_token'], max_age=new_token_info['expires_in'])

    return response