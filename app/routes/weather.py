from flask import Blueprint, request, jsonify
import requests
import os
import logging
from app.routes.spotify import create_playlist, add_tracks_to_playlist
from app.routes.spotify_auth import get_user_from_token
from flask_cors import cross_origin

weather_routes = Blueprint('weather_routes', __name__)

def filter_songs_by_weather(song_qualities, weather_condition, temperature):
    print("Inside filter_songs_by_weather")

    temperature = float(temperature)

    if temperature > 30:
        filtered_songs = [song for song in song_qualities if song['energy'] > 0.7 and song['valence'] > 0.7]
    elif temperature < 10:
        filtered_songs = [song for song in song_qualities if song['energy'] < 0.3 and song['valence'] < 0.3]
    elif weather_condition in ['Rain', 'Snow']:
        filtered_songs = [song for song in song_qualities if song['acousticness'] > 0.5]
    elif weather_condition == 'Clear':
        filtered_songs = [song for song in song_qualities if song['danceability'] > 0.7]
    else:
        filtered_songs = [song for song in song_qualities if 0.3 <= song['energy'] <= 0.7 and 0.3 <= song['valence'] <= 0.7]

    songs_to_use = filtered_songs if len(filtered_songs) >= 10 else song_qualities[:10]
    
    track_uris = [song['uri'] for song in songs_to_use]
    print("track_uris in filter song by weather", track_uris)  
    return track_uris
    
def get_api_key(api_name):
    return os.getenv(f'{api_name}_API_KEY')

def call_api(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_location_data(city):
    api_key = get_api_key('LOCATIONIQ')
    url = f"https://us1.locationiq.com/v1/search.php?key={api_key}&q={city}&format=json"
    return call_api(url)

def get_weather_data(lat, lon):
    api_key = get_api_key('OPENWEATHER')
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    return call_api(url)

def get_spotify_data(country, access_token):
    params = {'country': country}
    headers = {'Authorization': f'Bearer {access_token}'}
    url = "https://be-spotify-weather.onrender.com/search"
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise Exception("Failed to fetch Spotify data")
    return response.json()

def create_and_populate_playlist(playlist_name, track_uris,  access_token):
    print("inside create_and_populate_playlist")
    print("track_uris", track_uris)
    playlist_info = create_playlist(access_token, playlist_name)
    playlist_id = playlist_info['playlist_id']
    print("inside create and populate, playlist_id: ", playlist_id)
    print('back to popoulate playlist: track uris:', track_uris)
    add_tracks_to_playlist(playlist_id, track_uris, access_token)
    return playlist_id

@weather_routes.route('/weather', methods=['POST'])
@cross_origin(supports_credentials=True, origins='*')  
def get_weather():
    print("inside get_weather")
    try:
        city = request.json.get('city')
        print("city", city)
        if not city:
            return jsonify({'error': 'Invalid or missing city parameter'}), 400
        access_token = request.headers.get('Authorization').split(' ')[1]
        print("access_token", access_token)
        user = get_user_from_token(access_token)
        print("user", user)
        if not user:
            return jsonify({'error': 'Access token not found'}), 400

        location_data = get_location_data(city)
        weather_data = get_weather_data(location_data[0]['lat'], location_data[0]['lon'])
        playlist_name = f"{city} {weather_data['weather'][0]['description'].title()}"

       
        spotify_song_data = get_spotify_data(location_data[0]['display_name'].split(',')[-1].strip(), access_token)
        temperature = weather_data['main']['temp']
        weather_condition = weather_data['weather'][0]['main']
        track_uris = filter_songs_by_weather(spotify_song_data, weather_condition, temperature)
        print("track_uris saved from filter songs by weather before passed to create and populate playlist", track_uris)

        playlist_id = create_and_populate_playlist(playlist_name, track_uris, access_token)

        return jsonify({'temperature': weather_data['main']['temp'], 'playlist': playlist_id})
    except Exception as e:
        logging.error(f"Internal server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500