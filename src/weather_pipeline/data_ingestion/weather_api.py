"""
Weather API client for fetching weather data from various providers
"""
import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class WeatherAPIClient:
    """Client for fetching weather data from various API providers"""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openweathermap"):
        self.api_key = api_key or settings.weather_api.api_key
        self.provider = provider
        self.base_url = settings.weather_api.base_url
        self.timeout = settings.weather_api.timeout
        self.rate_limit = settings.weather_api.rate_limit
        self.last_request_time = 0
        
        if not self.api_key:
            raise ValueError("API key is required for weather data fetching")
    
    def _rate_limit_delay(self):
        """Implement rate limiting to respect API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 60 / self.rate_limit  # seconds between requests
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with error handling and rate limiting"""
        self._rate_limit_delay()
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    def get_current_weather(self, city: str, country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch current weather data for a specific city
        
        Args:
            city: City name
            country_code: Optional ISO 3166 country code
            
        Returns:
            Dictionary containing weather data
        """
        location = city
        if country_code:
            location = f"{city},{country_code}"
        
        params = {
            "q": location,
            "appid": self.api_key,
            "units": "metric"  # Use Celsius
        }
        
        url = f"{self.base_url}/weather"
        data = self._make_request(url, params)
        
        # Standardize the response format
        return self._standardize_current_weather(data)
    
    def get_current_weather_by_coords(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch current weather data by coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary containing weather data
        """
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        
        url = f"{self.base_url}/weather"
        data = self._make_request(url, params)
        
        return self._standardize_current_weather(data)
    
    def get_historical_weather(self, city: str, days: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch historical weather data (Note: This is a placeholder for paid API features)
        
        Args:
            city: City name
            days: Number of days of historical data
            
        Returns:
            List of weather data dictionaries
        """
        # For free tier, we'll simulate historical data fetching
        # In production, this would use historical weather API endpoints
        logger.warning("Historical weather data requires paid API access")
        return []
    
    def get_weather_forecast(self, city: str, days: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch weather forecast data
        
        Args:
            city: City name
            days: Number of days for forecast
            
        Returns:
            List of forecast data dictionaries
        """
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }
        
        url = f"{self.base_url}/forecast"
        data = self._make_request(url, params)
        
        return self._standardize_forecast_data(data)
    
    def _standardize_current_weather(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize current weather data format
        
        Args:
            raw_data: Raw API response
            
        Returns:
            Standardized weather data
        """
        try:
            return {
                "timestamp": datetime.utcnow(),
                "city": raw_data["name"],
                "country": raw_data["sys"]["country"],
                "latitude": raw_data["coord"]["lat"],
                "longitude": raw_data["coord"]["lon"],
                "temperature": raw_data["main"]["temp"],
                "feels_like": raw_data["main"]["feels_like"],
                "temperature_min": raw_data["main"]["temp_min"],
                "temperature_max": raw_data["main"]["temp_max"],
                "pressure": raw_data["main"]["pressure"],
                "humidity": raw_data["main"]["humidity"],
                "visibility": raw_data.get("visibility"),
                "wind_speed": raw_data.get("wind", {}).get("speed"),
                "wind_direction": raw_data.get("wind", {}).get("deg"),
                "cloudiness": raw_data["clouds"]["all"],
                "weather_main": raw_data["weather"][0]["main"],
                "weather_description": raw_data["weather"][0]["description"],
                "sunrise": datetime.fromtimestamp(raw_data["sys"]["sunrise"]),
                "sunset": datetime.fromtimestamp(raw_data["sys"]["sunset"]),
                "data_source": self.provider,
                "api_timestamp": datetime.fromtimestamp(raw_data["dt"])
            }
        except KeyError as e:
            logger.error(f"Failed to parse weather data: Missing key {e}")
            raise
    
    def _standardize_forecast_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Standardize forecast data format
        
        Args:
            raw_data: Raw API response
            
        Returns:
            List of standardized forecast data
        """
        forecasts = []
        
        try:
            for item in raw_data["list"]:
                forecast = {
                    "timestamp": datetime.utcnow(),
                    "forecast_time": datetime.fromtimestamp(item["dt"]),
                    "city": raw_data["city"]["name"],
                    "country": raw_data["city"]["country"],
                    "latitude": raw_data["city"]["coord"]["lat"],
                    "longitude": raw_data["city"]["coord"]["lon"],
                    "temperature": item["main"]["temp"],
                    "feels_like": item["main"]["feels_like"],
                    "temperature_min": item["main"]["temp_min"],
                    "temperature_max": item["main"]["temp_max"],
                    "pressure": item["main"]["pressure"],
                    "humidity": item["main"]["humidity"],
                    "wind_speed": item.get("wind", {}).get("speed"),
                    "wind_direction": item.get("wind", {}).get("deg"),
                    "cloudiness": item["clouds"]["all"],
                    "weather_main": item["weather"][0]["main"],
                    "weather_description": item["weather"][0]["description"],
                    "precipitation_probability": item.get("pop", 0) * 100,  # Convert to percentage
                    "data_source": self.provider,
                    "is_forecast": True
                }
                forecasts.append(forecast)
                
        except KeyError as e:
            logger.error(f"Failed to parse forecast data: Missing key {e}")
            raise
        
        return forecasts


class WeatherDataCollector:
    """High-level collector for gathering weather data from multiple sources"""
    
    def __init__(self):
        self.api_client = WeatherAPIClient()
        self.default_cities = [
            ("London", "GB"),
            ("New York", "US"),
            ("Tokyo", "JP"),
            ("Sydney", "AU"),
            ("Mumbai", "IN")
        ]
    
    def collect_current_weather_batch(self, cities: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """
        Collect current weather data for multiple cities
        
        Args:
            cities: List of (city, country_code) tuples
            
        Returns:
            List of weather data dictionaries
        """
        cities = cities or self.default_cities
        weather_data = []
        
        for city, country_code in cities:
            try:
                data = self.api_client.get_current_weather(city, country_code)
                weather_data.append(data)
                logger.info(f"Successfully collected weather data for {city}, {country_code}")
            except Exception as e:
                logger.error(f"Failed to collect weather data for {city}, {country_code}: {e}")
        
        return weather_data
    
    def collect_forecast_batch(self, cities: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
        """
        Collect forecast data for multiple cities
        
        Args:
            cities: List of (city, country_code) tuples
            
        Returns:
            List of forecast data dictionaries
        """
        cities = cities or self.default_cities
        forecast_data = []
        
        for city, country_code in cities:
            try:
                city_name = f"{city},{country_code}"
                forecasts = self.api_client.get_weather_forecast(city_name)
                forecast_data.extend(forecasts)
                logger.info(f"Successfully collected forecast data for {city}, {country_code}")
            except Exception as e:
                logger.error(f"Failed to collect forecast data for {city}, {country_code}: {e}")
        
        return forecast_data