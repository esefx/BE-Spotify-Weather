from dotenv import load_dotenv
import os

#load env variables from .env
load_dotenv()

#get api keys
LOCATION_API_KEY = os.getenv('LOCATIONIQ_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')