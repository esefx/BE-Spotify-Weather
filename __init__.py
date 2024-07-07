from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app, supports_credentials=True, origins='http://localhost:3000')
    if not test_config:
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
            "SQLALCHEMY_DATABASE_URI")
        # app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        #     "RENDER_DATABASE_URI")
    else:
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "SQLALCHEMY_TEST_DATABASE_URI")
        
    from models.user import User
    db.init_app(app)
    migrate.init_app(app, db)

    from routes.spotify_auth import spotify_auth_routes
    app.register_blueprint(spotify_auth_routes)

    from routes.spotify import spotify_routes
    app.register_blueprint(spotify_routes)

    from routes.weather import weather_routes
    app.register_blueprint(weather_routes)

    return app