from flask import Blueprint, request, jsonify
import requests
import os


weather_routes = Blueprint('weather_routes', __name__)

@weather_routes.route('/api/weather', methods=['POST'])
def get_weather():
    try:
        # Get city name from the request
        city = request.json.get('city')

        # Retrieve API keys from environment variables
        LOCATIONIQ_API_KEY = os.getenv('LOCATIONIQ_API_KEY')
        OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

        # Call LocationIQ API to get latitude and longitude
        locationiq_url = f"https://us1.locationiq.com/v1/search.php?key={LOCATIONIQ_API_KEY}&q={city}&format=json"
        locationiq_response = requests.get(locationiq_url)
        locationiq_data = locationiq_response.json()

        # Extract latitude and longitude 
        lat = locationiq_data[0]['lat']
        lon = locationiq_data[0]['lon']

        # Call OpenWeather API to get weather data using latitude and longitude
        openweather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        openweather_response = requests.get(openweather_url)
        openweather_data = openweather_response.json()

        # Extract temperature from OpenWeather response
        temperature = openweather_data['main']['temp']

        return jsonify({'temperature': temperature})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
