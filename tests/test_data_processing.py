"""
Tests for data processing module
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.weather_pipeline.data_processing.cleaner import WeatherDataCleaner
from src.weather_pipeline.data_processing.transformer import WeatherDataTransformer


class TestWeatherDataCleaner:
    """Test cases for WeatherDataCleaner"""
    
    @pytest.fixture
    def cleaner(self):
        """Create WeatherDataCleaner instance"""
        return WeatherDataCleaner()
    
    @pytest.fixture
    def sample_weather_data(self):
        """Sample weather data for testing"""
        return [
            {
                "timestamp": datetime.now(),
                "city": "London",
                "temperature": 15.5,
                "humidity": 72,
                "pressure": 1013,
                "wind_speed": 3.5,
                "latitude": 51.5074,
                "longitude": -0.1278
            },
            {
                "timestamp": datetime.now(),
                "city": "Paris",
                "temperature": 18.2,
                "humidity": 65,
                "pressure": 1020,
                "wind_speed": 2.1,
                "latitude": 48.8566,
                "longitude": 2.3522
            }
        ]
    
    @pytest.fixture
    def invalid_weather_data(self):
        """Invalid weather data for testing"""
        return [
            {
                "timestamp": datetime.now(),
                "city": "InvalidCity",
                "temperature": 150,  # Invalid temperature
                "humidity": 150,     # Invalid humidity
                "pressure": 500,     # Invalid pressure
                "latitude": 200,     # Invalid latitude
                "longitude": 200     # Invalid longitude
            },
            {
                # Missing required fields
                "city": "IncompleteCity",
                "temperature": 20
                # Missing timestamp and humidity
            }
        ]
    
    def test_clean_weather_data_valid(self, cleaner, sample_weather_data):
        """Test cleaning valid weather data"""
        result = cleaner.clean_weather_data(sample_weather_data)
        
        assert len(result) == 2
        assert all(record["city"] in ["London", "Paris"] for record in result)
        assert all(isinstance(record["temperature"], float) for record in result)
    
    def test_clean_weather_data_invalid(self, cleaner, invalid_weather_data):
        """Test cleaning invalid weather data"""
        result = cleaner.clean_weather_data(invalid_weather_data)
        
        # Should filter out invalid records
        assert len(result) < len(invalid_weather_data)
    
    def test_clean_single_record_valid(self, cleaner):
        """Test cleaning a single valid record"""
        record = {
            "timestamp": datetime.now(),
            "city": "London",
            "temperature": 15.5,
            "humidity": 72
        }
        
        result = cleaner._clean_single_record(record)
        
        assert result is not None
        assert result["city"] == "London"
        assert result["temperature"] == 15.5
    
    def test_clean_single_record_missing_required(self, cleaner):
        """Test cleaning record with missing required fields"""
        record = {
            "city": "London",
            "temperature": 15.5
            # Missing timestamp and humidity
        }
        
        result = cleaner._clean_single_record(record)
        
        assert result is None
    
    def test_clean_single_record_invalid_values(self, cleaner):
        """Test cleaning record with invalid values"""
        record = {
            "timestamp": datetime.now(),
            "city": "London",
            "temperature": 150,  # Invalid
            "humidity": 72,
            "latitude": 200      # Invalid
        }
        
        result = cleaner._clean_single_record(record)
        
        assert result is not None
        assert result["temperature"] is None  # Should be cleaned
        assert result["latitude"] is None     # Should be cleaned
        assert result["humidity"] == 72       # Should remain valid
    
    def test_detect_outliers_iqr(self, cleaner):
        """Test outlier detection using IQR method"""
        df = pd.DataFrame({
            "temperature": [10, 12, 11, 13, 100, 12, 11]  # 100 is outlier
        })
        
        outliers = cleaner.detect_outliers(df, "temperature", method="iqr")
        
        assert outliers.sum() > 0  # Should detect at least one outlier
        assert outliers.iloc[4] == True  # 100 should be detected as outlier
    
    def test_detect_outliers_zscore(self, cleaner):
        """Test outlier detection using z-score method"""
        df = pd.DataFrame({
            "temperature": [10, 12, 11, 13, 100, 12, 11]  # 100 is outlier
        })
        
        outliers = cleaner.detect_outliers(df, "temperature", method="zscore")
        
        assert outliers.sum() > 0  # Should detect at least one outlier
    
    def test_handle_missing_values_interpolate(self, cleaner):
        """Test missing value handling with interpolation"""
        df = pd.DataFrame({
            "temperature": [10, np.nan, 12, np.nan, 14],
            "humidity": [50, 55, np.nan, 65, 70]
        })
        
        result = cleaner.handle_missing_values(df, strategy="interpolate")
        
        assert result["temperature"].isnull().sum() == 0
        assert result["humidity"].isnull().sum() == 0
    
    def test_remove_duplicates(self, cleaner):
        """Test duplicate removal"""
        df = pd.DataFrame({
            "city": ["London", "London", "Paris"],
            "timestamp": [datetime.now()] * 3,
            "temperature": [15, 15, 18],
            "humidity": [70, 70, 65]
        })
        
        result = cleaner.remove_duplicates(df)
        
        assert len(result) == 2  # Should remove one duplicate


class TestWeatherDataTransformer:
    """Test cases for WeatherDataTransformer"""
    
    @pytest.fixture
    def transformer(self):
        """Create WeatherDataTransformer instance"""
        return WeatherDataTransformer()
    
    @pytest.fixture
    def sample_dataframe(self):
        """Sample DataFrame for testing"""
        data = {
            "timestamp": pd.date_range(start="2024-01-01", periods=24, freq="H"),
            "city": ["London"] * 24,
            "temperature": np.random.normal(15, 5, 24),
            "humidity": np.random.uniform(40, 80, 24),
            "pressure": np.random.normal(1013, 10, 24),
            "wind_speed": np.random.uniform(0, 10, 24),
            "wind_direction": np.random.uniform(0, 360, 24),
            "weather_main": ["Clear", "Clouds", "Rain"] * 8
        }
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df
    
    def test_transform_to_dataframe(self, transformer):
        """Test transformation from list to DataFrame"""
        data = [
            {
                "timestamp": "2024-01-01 12:00:00",
                "city": "London",
                "temperature": 15.5,
                "humidity": 72
            },
            {
                "timestamp": "2024-01-01 13:00:00",
                "city": "Paris",
                "temperature": 18.2,
                "humidity": 65
            }
        ]
        
        result = transformer.transform_to_dataframe(data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.index.name == "timestamp"
        assert "city" in result.columns
    
    def test_add_derived_features(self, transformer, sample_dataframe):
        """Test addition of derived features"""
        result = transformer.add_derived_features(sample_dataframe)
        
        # Check for new derived columns
        assert "hour" in result.columns
        assert "month" in result.columns
        assert "season" in result.columns
        assert "wind_u" in result.columns
        assert "wind_v" in result.columns
        
        # Check that original columns are preserved
        assert "temperature" in result.columns
        assert "humidity" in result.columns
    
    def test_aggregate_data_daily(self, transformer, sample_dataframe):
        """Test daily aggregation"""
        result = transformer.aggregate_data(sample_dataframe, frequency="D")
        
        assert len(result) == 1  # Should have one day
        assert "temperature_mean" in result.columns
        assert "temperature_min" in result.columns
        assert "temperature_max" in result.columns
    
    def test_calculate_rolling_statistics(self, transformer, sample_dataframe):
        """Test rolling statistics calculation"""
        result = transformer.calculate_rolling_statistics(sample_dataframe, window=6)
        
        # Check for rolling columns
        rolling_cols = [col for col in result.columns if "rolling" in col]
        assert len(rolling_cols) > 0
        
        # Check that rolling mean exists for temperature
        assert "temperature_rolling_mean" in result.columns
    
    def test_calculate_heat_index(self, transformer):
        """Test heat index calculation"""
        temperature = pd.Series([25, 30, 35])
        humidity = pd.Series([50, 70, 80])
        
        heat_index = transformer._calculate_heat_index(temperature, humidity)
        
        assert isinstance(heat_index, pd.Series)
        assert len(heat_index) == 3
        assert all(heat_index >= temperature)  # Heat index should be >= temperature
    
    def test_calculate_comfort_index(self, transformer):
        """Test comfort index calculation"""
        temperature = pd.Series([20, 25, 30])
        humidity = pd.Series([50, 60, 70])
        wind_speed = pd.Series([2, 3, 4])
        
        comfort = transformer._calculate_comfort_index(temperature, humidity, wind_speed)
        
        assert isinstance(comfort, pd.Series)
        assert len(comfort) == 3
        assert all((comfort >= 0) & (comfort <= 100))  # Should be in 0-100 range
    
    def test_get_season(self, transformer):
        """Test season determination"""
        months = pd.Series([1, 4, 7, 10])  # Jan, Apr, Jul, Oct
        
        seasons = transformer._get_season(months)
        
        expected = ["Winter", "Spring", "Summer", "Autumn"]
        assert list(seasons) == expected
    
    def test_categorize_weather(self, transformer):
        """Test weather categorization"""
        weather_conditions = pd.Series(["Clear", "Rain", "Clouds", "Thunderstorm", "Unknown"])
        
        categories = transformer._categorize_weather(weather_conditions)
        
        assert categories.iloc[0] == "Clear"
        assert categories.iloc[1] == "Precipitation"
        assert categories.iloc[2] == "Cloudy"
        assert categories.iloc[3] == "Severe"
        assert categories.iloc[4] == "Other"


if __name__ == "__main__":
    pytest.main([__file__])