from dotenv import load_dotenv
import os
from flask import Flask
from flask_cors import CORS
from flask_session import Session
from routes.weather import weather_routes
from routes.spotify import spotify_routes
import requests


# Load env variables from .env
load_dotenv()

# Get location API keys
LOCATION_API_KEY = os.getenv('LOCATIONIQ_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
# Get Spotify API keys
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')
# Flask app secret key
SECRET_KEY = os.getenv('SECRET_KEY')


# Initialize Flask app
app = Flask(__name__)
CORS(app)
app.secret_key = SECRET_KEY  # Use the secret key from environment variables

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'  # You can use other session types if needed
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'session:'
app.config['SESSION_FILE_DIR'] = './.flask_session/'  # Directory to store session files

# Initialize Flask-Session
Session(app)

# Register all routes
app.register_blueprint(weather_routes)
app.register_blueprint(spotify_routes)

# Initialize home route
@app.route('/')
def index():
    return "Welcome to my Spotify App <a href='/login'> Login with Spotify </a>"

if __name__ == '__main__':
    app.run(debug=True)
