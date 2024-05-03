from dotenv import load_dotenv
import os
from flask import Flask
from flask_cors import CORS
from routes.weather import weather_routes

#load env variables from .env
load_dotenv()

#get api keys
LOCATION_API_KEY = os.getenv('LOCATIONIQ_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

#initialize flask app
app = Flask(__name__)
CORS(app)

#register all routes
app.register_blueprint(weather_routes)

if __name__ == '__main__':
    app.run(debug=True)