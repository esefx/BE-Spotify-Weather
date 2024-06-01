from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from models.sessions import db
from flask_migrate import Migrate

# Get Spotify API keys
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SPOTIFY_SCOPES = os.getenv('SPOTIFY_SCOPES')
# Flask app secret key
SECRET_KEY = os.getenv('SECRET_KEY')


def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    CORS(app)
    app.secret_key = SECRET_KEY  # Use the secret key from environment variables

    # Database configs
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate = Migrate(app, db)
    print(os.getenv('SQLALCHEMY_DATABASE_URI'))

    # Import and register all routes
    from routes.weather import weather_routes
    from routes.spotify import spotify_routes
    app.register_blueprint(weather_routes)
    app.register_blueprint(spotify_routes)

    # Initialize home route
    @app.route('/')
    def index():
        return "Welcome to my Spotify App <a href='/login'> Login with Spotify </a>"

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()