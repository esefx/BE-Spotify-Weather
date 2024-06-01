from flask import Blueprint, request, jsonify
import requests
import os
import logging
from models.sessions import Session

logging.basicConfig(level=logging.DEBUG)

weather_routes = Blueprint('weather_routes', __name__)

def filter_songs_by_weather(weather_data, song_qualities):
    temperature = weather_data['main']['temp']
    weather_condition = weather_data['weather'][0]['main']

    if temperature > 30:
        return [song for song in song_qualities if song['energy'] > 0.7 and song['valence'] > 0.7]
    elif temperature < 10:
        return [song for song in song_qualities if song['energy'] < 0.3 and song['valence'] < 0.3]
    elif weather_condition in ['Rain', 'Snow']:
        return [song for song in song_qualities if song['acousticness'] > 0.5]
    elif weather_condition == 'Clear':
        return [song for song in song_qualities if song['danceability'] > 0.7]
    else:
        return [song for song in song_qualities if 0.3 <= song['energy'] <= 0.7 and 0.3 <= song['valence'] <= 0.7]

@weather_routes.route('/weather', methods=['POST'])
def get_weather():
    try:
        # Get the access token from the request headers
        auth_header = request.headers.get('Authorization')
        if auth_header:
            access_token = auth_header.split(' ')[1]
        else:
            return jsonify({"error": "No access token provided", 'access token': access_token}), 401
        
        # Query the database for the session
        user_session = Session.query.filter_by(access_token=access_token).first()
        if not user_session:
            return jsonify({"error": "User not authenticated", "user session": user_session}), 401

        # Get the user_id from the session
        user_id = user_session.user_id

        city = request.json.get('city')
        if not city or not isinstance(city, str):
            return jsonify({'error': 'Invalid or missing city parameter'}), 400

        LOCATIONIQ_API_KEY = os.getenv('LOCATIONIQ_API_KEY')
        OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

        locationiq_url = f"https://us1.locationiq.com/v1/search.php?key={LOCATIONIQ_API_KEY}&q={city}&format=json"
        logging.debug(f"Calling LocationIQ API with URL: {locationiq_url}")
        locationiq_response = requests.get(locationiq_url)
        locationiq_response.raise_for_status()
        locationiq_data = locationiq_response.json()

        lat = locationiq_data[0]['lat']
        lon = locationiq_data[0]['lon']
        location_name = locationiq_data[0]['display_name']
        name_list = location_name.split(',')
        country = name_list[-1].strip()

        openweather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        logging.debug(f"Calling OpenWeather API with URL: {openweather_url}")
        openweather_response = requests.get(openweather_url)
        openweather_response.raise_for_status()
        openweather_data = openweather_response.json()
        # Define playlist name
        weather_description = openweather_data['weather'][0]['description']
        playlist_name = f"{city} {weather_description}"

        temperature = openweather_data['main']['temp']

        headers = {'Authorization': f'Bearer {access_token}'}
        search_response = requests.get(f"http://127.0.0.1:5000/search?country={country}", headers=headers)
        if search_response.status_code != 200:
            return jsonify({"error": "Failed to fetch Spotify data"}), search_response.status_code

        song_qualities = search_response.json()

        # Filter the songs based on the weather
        playlist = filter_songs_by_weather(openweather_data, song_qualities)

        # Create a new Spotify playlist

        response = requests.post(
        'http://localhost:5000/create-playlist',
        json={'playlist_name': playlist_name, 'access_token': access_token}
        )

        if response.status_code != 200:
            return jsonify({"error": "Failed to create playlist"}), response.status_code

        playlist_id = response.json()['playlist_id']


        # Add tracks to the new Spotify playlist
        track_uris = [song['uri'] for song in playlist]

        # Make a POST request to the /add-tracks route
        response = requests.post(
            'http://localhost:5000/add-tracks',
            json={'playlist_id': playlist_id, 'tracks': track_uris}
        )

        if response.status_code != 200:
            logging.error(f"Failed to add tracks to playlist: {response.content}")
            return jsonify({'error': 'Failed to add tracks to playlist'}), response.status_code

        playlist_id = response.json()['playlist_id']

        return jsonify({'temperature': temperature, 'playlist': playlist_id})
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
