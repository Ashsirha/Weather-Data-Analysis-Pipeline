"""
Tests for data ingestion module
"""
import pytest
import unittest.mock as mock
from datetime import datetime
from src.weather_pipeline.data_ingestion.weather_api import WeatherAPIClient, WeatherDataCollector


class TestWeatherAPIClient:
    """Test cases for WeatherAPIClient"""
    
    @pytest.fixture
    def api_client(self):
        """Create API client with mock API key"""
        return WeatherAPIClient(api_key="test_api_key")
    
    @pytest.fixture
    def mock_response_data(self):
        """Mock API response data"""
        return {
            "name": "London",
            "sys": {"country": "GB", "sunrise": 1640000000, "sunset": 1640030000},
            "coord": {"lat": 51.5074, "lon": -0.1278},
            "main": {
                "temp": 15.5,
                "feels_like": 14.2,
                "temp_min": 13.0,
                "temp_max": 18.0,
                "pressure": 1013,
                "humidity": 72
            },
            "wind": {"speed": 3.5, "deg": 250},
            "clouds": {"all": 75},
            "visibility": 10000,
            "weather": [{"main": "Clouds", "description": "broken clouds"}],
            "dt": 1640010000
        }
    
    def test_api_client_initialization(self):
        """Test API client initialization"""
        client = WeatherAPIClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.provider == "openweathermap"
    
    def test_api_client_no_key_raises_error(self):
        """Test that missing API key raises error"""
        with pytest.raises(ValueError, match="API key is required"):
            WeatherAPIClient(api_key=None)
    
    @mock.patch('requests.get')
    def test_get_current_weather_success(self, mock_get, api_client, mock_response_data):
        """Test successful weather data retrieval"""
        mock_response = mock.Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = api_client.get_current_weather("London", "GB")
        
        assert result["city"] == "London"
        assert result["country"] == "GB"
        assert result["temperature"] == 15.5
        assert result["humidity"] == 72
        assert isinstance(result["timestamp"], datetime)
    
    @mock.patch('requests.get')
    def test_get_current_weather_api_error(self, mock_get, api_client):
        """Test API error handling"""
        mock_get.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            api_client.get_current_weather("London", "GB")
    
    def test_standardize_current_weather(self, api_client, mock_response_data):
        """Test weather data standardization"""
        result = api_client._standardize_current_weather(mock_response_data)
        
        assert result["city"] == "London"
        assert result["country"] == "GB"
        assert result["temperature"] == 15.5
        assert result["humidity"] == 72
        assert result["data_source"] == "openweathermap"
        assert isinstance(result["timestamp"], datetime)
    
    def test_standardize_current_weather_missing_key(self, api_client):
        """Test standardization with missing keys"""
        incomplete_data = {"name": "London"}
        
        with pytest.raises(KeyError):
            api_client._standardize_current_weather(incomplete_data)


class TestWeatherDataCollector:
    """Test cases for WeatherDataCollector"""
    
    @pytest.fixture
    def collector(self):
        """Create data collector with mocked API client"""
        with mock.patch('src.weather_pipeline.data_ingestion.weather_api.WeatherAPIClient'):
            return WeatherDataCollector()
    
    @mock.patch('src.weather_pipeline.data_ingestion.weather_api.WeatherAPIClient')
    def test_collect_current_weather_batch_success(self, mock_client_class):
        """Test successful batch collection"""
        mock_client = mock.Mock()
        mock_client.get_current_weather.return_value = {
            "city": "London",
            "temperature": 15.5,
            "humidity": 72
        }
        mock_client_class.return_value = mock_client
        
        collector = WeatherDataCollector()
        cities = [("London", "GB"), ("Paris", "FR")]
        
        result = collector.collect_current_weather_batch(cities)
        
        assert len(result) == 2
        assert mock_client.get_current_weather.call_count == 2
    
    @mock.patch('src.weather_pipeline.data_ingestion.weather_api.WeatherAPIClient')
    def test_collect_current_weather_batch_partial_failure(self, mock_client_class):
        """Test batch collection with partial failures"""
        mock_client = mock.Mock()
        mock_client.get_current_weather.side_effect = [
            {"city": "London", "temperature": 15.5},  # Success
            Exception("API Error")  # Failure
        ]
        mock_client_class.return_value = mock_client
        
        collector = WeatherDataCollector()
        cities = [("London", "GB"), ("InvalidCity", "XX")]
        
        result = collector.collect_current_weather_batch(cities)
        
        assert len(result) == 1  # Only successful one
        assert result[0]["city"] == "London"


if __name__ == "__main__":
    pytest.main([__file__])