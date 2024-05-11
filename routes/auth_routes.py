from flask import Blueprint, redirect, request, session, url_for
from services.spotify_services import get_spotify_auth_url, get_spotify_tokens

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/login')
def login():
    auth_url = get_spotify_auth_url()
    return redirect(auth_url)

@auth_routes.route('/callback')
def callback():
    code = request.args.get('code')
    tokens = get_spotify_tokens(code)
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens['refresh_token']
    # Redirect to a success page or perform additional actions
    return redirect(url_for('main.home'))