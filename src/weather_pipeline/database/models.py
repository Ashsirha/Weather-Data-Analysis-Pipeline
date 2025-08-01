"""
Database models for weather data storage
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class WeatherData(Base):
    """Model for storing current weather data"""
    
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Timestamp information
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    api_timestamp = Column(DateTime, nullable=True)
    
    # Location information
    city = Column(String(100), nullable=False)
    country = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Temperature data
    temperature = Column(Float, nullable=False)  # Celsius
    feels_like = Column(Float, nullable=True)
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    
    # Atmospheric data
    pressure = Column(Float, nullable=True)  # hPa
    humidity = Column(Float, nullable=True)  # Percentage
    visibility = Column(Float, nullable=True)  # Meters
    
    # Wind data
    wind_speed = Column(Float, nullable=True)  # m/s
    wind_direction = Column(Float, nullable=True)  # Degrees
    
    # Cloud and weather data
    cloudiness = Column(Float, nullable=True)  # Percentage
    weather_main = Column(String(50), nullable=True)
    weather_description = Column(String(200), nullable=True)
    
    # Sun data
    sunrise = Column(DateTime, nullable=True)
    sunset = Column(DateTime, nullable=True)
    
    # Metadata
    data_source = Column(String(50), nullable=False, default="openweathermap")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Add indexes for better query performance
    __table_args__ = (
        Index("idx_weather_city_timestamp", "city", "timestamp"),
        Index("idx_weather_timestamp", "timestamp"),
        Index("idx_weather_location", "latitude", "longitude"),
    )
    
    def __repr__(self):
        return f"<WeatherData(city='{self.city}', timestamp='{self.timestamp}', temperature={self.temperature})>"


class ForecastData(Base):
    """Model for storing weather forecast data"""
    
    __tablename__ = "forecast_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Timestamp information
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)  # When data was collected
    forecast_time = Column(DateTime, nullable=False)  # Time the forecast is for
    
    # Location information
    city = Column(String(100), nullable=False)
    country = Column(String(10), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Temperature data
    temperature = Column(Float, nullable=False)
    feels_like = Column(Float, nullable=True)
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    
    # Atmospheric data
    pressure = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    
    # Wind data
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)
    
    # Cloud and weather data
    cloudiness = Column(Float, nullable=True)
    weather_main = Column(String(50), nullable=True)
    weather_description = Column(String(200), nullable=True)
    precipitation_probability = Column(Float, nullable=True)  # Percentage
    
    # Metadata
    data_source = Column(String(50), nullable=False, default="openweathermap")
    is_forecast = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Add indexes for better query performance
    __table_args__ = (
        Index("idx_forecast_city_forecast_time", "city", "forecast_time"),
        Index("idx_forecast_forecast_time", "forecast_time"),
        Index("idx_forecast_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<ForecastData(city='{self.city}', forecast_time='{self.forecast_time}', temperature={self.temperature})>"


class ProcessedWeatherData(Base):
    """Model for storing processed and aggregated weather data"""
    
    __tablename__ = "processed_weather_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Timestamp and aggregation info
    timestamp = Column(DateTime, nullable=False)
    aggregation_period = Column(String(10), nullable=False)  # 'hourly', 'daily', 'weekly', 'monthly'
    
    # Location information
    city = Column(String(100), nullable=False)
    country = Column(String(10), nullable=True)
    
    # Temperature statistics
    temperature_mean = Column(Float, nullable=True)
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    temperature_std = Column(Float, nullable=True)
    
    # Other weather statistics
    humidity_mean = Column(Float, nullable=True)
    pressure_mean = Column(Float, nullable=True)
    wind_speed_mean = Column(Float, nullable=True)
    wind_speed_max = Column(Float, nullable=True)
    cloudiness_mean = Column(Float, nullable=True)
    
    # Derived features
    temperature_range = Column(Float, nullable=True)
    comfort_index_mean = Column(Float, nullable=True)
    
    # Count of original records
    record_count = Column(Integer, nullable=False, default=1)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Add indexes
    __table_args__ = (
        Index("idx_processed_city_timestamp_period", "city", "timestamp", "aggregation_period"),
        Index("idx_processed_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<ProcessedWeatherData(city='{self.city}', period='{self.aggregation_period}', timestamp='{self.timestamp}')>"


class WeatherAlert(Base):
    """Model for storing weather alerts and anomalies"""
    
    __tablename__ = "weather_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Alert information
    alert_type = Column(String(50), nullable=False)  # 'anomaly', 'extreme', 'forecast_warning'
    severity = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Location and time
    city = Column(String(100), nullable=False)
    country = Column(String(10), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    
    # Alert conditions
    parameter = Column(String(50), nullable=True)  # What parameter triggered the alert
    threshold_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Add indexes
    __table_args__ = (
        Index("idx_alerts_city_timestamp", "city", "timestamp"),
        Index("idx_alerts_active", "is_active"),
        Index("idx_alerts_severity", "severity"),
    )
    
    def __repr__(self):
        return f"<WeatherAlert(type='{self.alert_type}', city='{self.city}', severity='{self.severity}')>"