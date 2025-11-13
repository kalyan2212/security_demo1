# Weather Route Checker 🌤️

A three-tier web application that provides weather information along a calculated route between two locations.

## Features

- **Route Calculation**: Uses Google Maps API to calculate driving routes between two addresses
- **Weather Data**: Fetches real-time weather information for waypoints along the route
- **Query Logging**: Stores all queries and results in MongoDB for analytics
- **Beautiful UI**: Clean, responsive frontend with gradient design
- **No Authentication Required**: Simple, open access for demonstration purposes

## Architecture

### Frontend
- **Technology**: HTML, CSS, JavaScript (Vanilla)
- **Location**: `frontend/index.html`
- **Features**: 
  - Responsive design
  - Beautiful gradient UI
  - Real-time API integration
  - Error handling and loading states

### Backend
- **Technology**: Python Flask REST API
- **Location**: `backend/app.py`
- **Endpoints**:
  - `POST /api/route_weather` - Main endpoint for route weather queries
  - `GET /api/health` - Health check endpoint
- **Integrations**:
  - Google Maps API for route calculation
  - OpenWeatherMap API (Weather.com alternative) for weather data
  - MongoDB for query logging

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- MongoDB (optional, application works without it but won't log queries)
- Google Maps API key
- OpenWeatherMap API key (or Weather.com API key)

### 1. Clone the Repository

```bash
git clone https://github.com/kalyan2212/security_demo1.git
cd security_demo1
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Get API Keys

#### Google Maps API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Directions API" and "Geocoding API"
4. Create credentials (API Key)
5. Copy the API key

#### OpenWeatherMap API Key
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Generate an API key
4. Copy the API key

Note: The application uses OpenWeatherMap API as a Weather.com alternative. If you have a Weather.com API key, you can modify the `get_weather_data` function in `backend/app.py` to use it instead.

#### MongoDB (Optional)
- Install MongoDB locally or use MongoDB Atlas (cloud)
- Default connection string: `mongodb://localhost:27017/`
- For Atlas, use your connection string

### 4. Set Environment Variables

#### Linux/Mac:
```bash
export GOOGLE_MAPS_KEY="your_google_maps_api_key_here"
export WEATHER_API_KEY="your_openweathermap_api_key_here"
export MONGO_URI="mongodb://localhost:27017/"  # Optional
```

#### Windows (Command Prompt):
```cmd
set GOOGLE_MAPS_KEY=your_google_maps_api_key_here
set WEATHER_API_KEY=your_openweathermap_api_key_here
set MONGO_URI=mongodb://localhost:27017/
```

#### Windows (PowerShell):
```powershell
$env:GOOGLE_MAPS_KEY="your_google_maps_api_key_here"
$env:WEATHER_API_KEY="your_openweathermap_api_key_here"
$env:MONGO_URI="mongodb://localhost:27017/"
```

### 5. Start the Backend Server

```bash
cd backend
python app.py
```

The backend server will start on `http://localhost:5000`

### 6. Open the Frontend

Open `frontend/index.html` in your web browser. You can:
- Simply double-click the file, or
- Use a local web server:
  ```bash
  cd frontend
  python -m http.server 8000
  ```
  Then open `http://localhost:8000` in your browser

## Usage

1. Enter a starting location (e.g., "New York, NY")
2. Enter a destination (e.g., "Boston, MA")
3. Click "Get Weather Route"
4. View the route information and weather data for waypoints along the route

## API Documentation

### POST /api/route_weather

Calculate route and get weather data.

**Request Body:**
```json
{
  "start_address": "New York, NY",
  "end_address": "Boston, MA"
}
```

**Response:**
```json
{
  "success": true,
  "start_address": "New York, NY",
  "end_address": "Boston, MA",
  "distance": "215 mi",
  "duration": "3 hours 45 mins",
  "weather_data": [
    {
      "location": "New York, NY",
      "lat": 40.7128,
      "lon": -74.0060,
      "weather": {
        "temperature": "22°C",
        "conditions": "Clear",
        "description": "clear sky",
        "humidity": "65%",
        "wind_speed": "3.5 m/s"
      }
    }
  ]
}
```

### GET /api/health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "google_maps_configured": true,
  "weather_api_configured": true,
  "mongodb_connected": true
}
```

## Configuration

All configuration is done via environment variables:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GOOGLE_MAPS_KEY` | Yes | Google Maps API key | None |
| `WEATHER_API_KEY` | Yes | OpenWeatherMap API key | None |
| `MONGO_URI` | No | MongoDB connection string | `mongodb://localhost:27017/` |
| `PORT` | No | Backend server port | `5000` |

## Project Structure

```
security_demo1/
├── backend/
│   └── app.py              # Flask backend application
├── frontend/
│   └── index.html          # Frontend HTML page
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Deployment

### Production Deployment with Gunicorn

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment (Optional)

Create a `Dockerfile` in the backend directory:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend/app.py .
ENV PORT=5000
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Troubleshooting

### "Google Maps API not configured" error
- Ensure `GOOGLE_MAPS_KEY` environment variable is set correctly
- Verify the API key is valid and has the Directions API enabled

### "Weather API key not configured" error
- Ensure `WEATHER_API_KEY` environment variable is set correctly
- Verify the API key is valid and active

### MongoDB connection issues
- MongoDB connection is optional
- Check if MongoDB is running: `mongod --version`
- Verify the `MONGO_URI` is correct

### CORS errors in frontend
- Ensure backend server is running
- Check that API_BASE_URL in `frontend/index.html` matches your backend URL
- For development, the backend has CORS enabled

## Security Notes

- **API Keys**: Never commit API keys to version control
- **Environment Variables**: Always use environment variables for sensitive data
- **Production**: In production, implement rate limiting and authentication
- **HTTPS**: Use HTTPS in production environments

## License

This project is for demonstration purposes.

## Contributing

This is a demonstration project. Feel free to fork and modify for your needs.
