from dotenv import load_dotenv
import os
from flask import Flask
from flask_cors import CORS
from routes.weather import weather_routes
from routes.auth_routes import auth_routes

#load env variables from .env
load_dotenv()

#get location api keys
LOCATION_API_KEY = os.getenv('LOCATIONIQ_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
#get spotify api keys
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')
#flask app secret key
SECRET_KEY = os.getenv('SECRET_KEY')


#initialize flask app
app = Flask(__name__)
CORS(app)

#register all routes
app.register_blueprint(weather_routes)
app.register_blueprint(auth_routes)

if __name__ == '__main__':
    app.run(debug=True)