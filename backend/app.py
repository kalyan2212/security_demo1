"""
Flask Backend API for Weather Route Application

This application provides a REST API endpoint that:
1. Accepts start and end addresses
2. Uses Google Maps API to calculate route waypoints
3. Fetches weather data for each waypoint using Weather.com API
4. Logs all queries and results to MongoDB
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import googlemaps
import requests
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Environment variables
GOOGLE_MAPS_KEY = os.environ.get('GOOGLE_MAPS_KEY', '')
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '')
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')

# Initialize clients
gmaps = None
mongo_client = None
db = None

def init_google_maps():
    """Initialize Google Maps client"""
    global gmaps
    if GOOGLE_MAPS_KEY:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_KEY)
        logger.info("Google Maps client initialized")
    else:
        logger.warning("GOOGLE_MAPS_KEY not set")

def init_mongodb():
    """Initialize MongoDB connection"""
    global mongo_client, db
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        mongo_client.admin.command('ping')
        db = mongo_client['weather_route_db']
        logger.info("MongoDB connection established")
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {e}")
        mongo_client = None
        db = None
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {e}")
        mongo_client = None
        db = None

def get_weather_data(lat, lon):
    """
    Fetch weather data for a given location using Weather.com API
    
    Args:
        lat: Latitude
        lon: Longitude
    
    Returns:
        dict: Weather data or error information
    """
    if not WEATHER_API_KEY:
        return {
            'error': 'Weather API key not configured',
            'temperature': 'N/A',
            'conditions': 'N/A',
            'description': 'Weather API key not available'
        }
    
    try:
        # Weather.com API endpoint (using OpenWeatherMap as a commonly used alternative)
        # Note: Replace with actual Weather.com API if specific endpoint is provided
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': WEATHER_API_KEY,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            'temperature': f"{data['main']['temp']}°C",
            'conditions': data['weather'][0]['main'],
            'description': data['weather'][0]['description'],
            'humidity': f"{data['main']['humidity']}%",
            'wind_speed': f"{data['wind']['speed']} m/s"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        return {
            'error': 'Unable to fetch weather data',
            'temperature': 'N/A',
            'conditions': 'Error fetching weather data'
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_weather_data: {e}")
        return {
            'error': 'Unable to process weather data',
            'temperature': 'N/A',
            'conditions': 'Error processing weather data'
        }

def log_to_mongodb(query_data):
    """
    Log query and results to MongoDB
    
    Args:
        query_data: Dictionary containing query information
    """
    if db is not None:
        try:
            collection = db['query_logs']
            query_data['timestamp'] = datetime.utcnow()
            collection.insert_one(query_data)
            logger.info("Query logged to MongoDB")
        except Exception as e:
            logger.error(f"Error logging to MongoDB: {e}")
    else:
        logger.warning("MongoDB not available, skipping log")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'google_maps_configured': bool(GOOGLE_MAPS_KEY),
        'weather_api_configured': bool(WEATHER_API_KEY),
        'mongodb_connected': db is not None
    })

@app.route('/api/route_weather', methods=['POST'])
def route_weather():
    """
    Main endpoint for route weather queries
    
    Expects JSON payload:
    {
        "start_address": "Start location",
        "end_address": "End location"
    }
    
    Returns:
    {
        "success": true,
        "route": [...],
        "weather_data": [...]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        start_address = data.get('start_address', '').strip()
        end_address = data.get('end_address', '').strip()
        
        if not start_address or not end_address:
            return jsonify({
                'success': False,
                'error': 'Both start_address and end_address are required'
            }), 400
        
        # Check if Google Maps is configured
        if not gmaps:
            return jsonify({
                'success': False,
                'error': 'Google Maps API not configured. Please set GOOGLE_MAPS_KEY environment variable.'
            }), 503
        
        # Get directions from Google Maps
        try:
            directions_result = gmaps.directions(
                start_address,
                end_address,
                mode="driving"
            )
            
            if not directions_result:
                return jsonify({
                    'success': False,
                    'error': 'No route found between the specified addresses'
                }), 404
            
        except googlemaps.exceptions.ApiError as e:
            logger.error(f"Google Maps API error: {e}")
            return jsonify({
                'success': False,
                'error': 'Google Maps API error. Please check your API key and try again.'
            }), 500
        except Exception as e:
            logger.error(f"Error getting directions: {e}")
            return jsonify({
                'success': False,
                'error': 'Error calculating route. Please verify your addresses and try again.'
            }), 500
        
        # Extract waypoints from the route
        route = directions_result[0]
        legs = route['legs']
        
        waypoints = []
        weather_data = []
        
        # Add start location
        start_location = legs[0]['start_location']
        waypoints.append({
            'address': legs[0]['start_address'],
            'lat': start_location['lat'],
            'lon': start_location['lng']
        })
        
        # Add intermediate waypoints (every few steps to avoid too many requests)
        for leg in legs:
            steps = leg['steps']
            # Sample waypoints - take every 5th step or fewer if route is short
            step_interval = max(1, len(steps) // 5) if len(steps) > 5 else len(steps)
            
            for i in range(0, len(steps), step_interval):
                step = steps[i]
                end_loc = step['end_location']
                waypoints.append({
                    'address': step.get('html_instructions', 'Waypoint'),
                    'lat': end_loc['lat'],
                    'lon': end_loc['lng']
                })
        
        # Add end location
        end_location = legs[-1]['end_location']
        waypoints.append({
            'address': legs[-1]['end_address'],
            'lat': end_location['lat'],
            'lon': end_location['lng']
        })
        
        # Remove duplicate waypoints (keep unique lat/lon combinations)
        unique_waypoints = []
        seen_coords = set()
        for wp in waypoints:
            coord_key = (round(wp['lat'], 4), round(wp['lon'], 4))
            if coord_key not in seen_coords:
                seen_coords.add(coord_key)
                unique_waypoints.append(wp)
        
        # Limit waypoints to avoid too many API calls
        if len(unique_waypoints) > 10:
            # Keep start, end, and evenly distributed middle points
            step = len(unique_waypoints) // 9
            selected = [unique_waypoints[0]]  # Start
            for i in range(step, len(unique_waypoints) - 1, step):
                selected.append(unique_waypoints[i])
            selected.append(unique_waypoints[-1])  # End
            unique_waypoints = selected
        
        # Fetch weather for each waypoint
        for waypoint in unique_waypoints:
            weather = get_weather_data(waypoint['lat'], waypoint['lon'])
            weather_data.append({
                'location': waypoint['address'],
                'lat': waypoint['lat'],
                'lon': waypoint['lon'],
                'weather': weather
            })
        
        # Prepare response
        response_data = {
            'success': True,
            'start_address': start_address,
            'end_address': end_address,
            'distance': legs[0].get('distance', {}).get('text', 'N/A'),
            'duration': legs[0].get('duration', {}).get('text', 'N/A'),
            'weather_data': weather_data
        }
        
        # Log to MongoDB
        log_data = {
            'start_address': start_address,
            'end_address': end_address,
            'waypoint_count': len(unique_waypoints),
            'response': response_data
        }
        log_to_mongodb(log_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in route_weather: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error. Please try again later.'
        }), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize services
    init_google_maps()
    init_mongodb()
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
