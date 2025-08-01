"""
Data transformation utilities for weather data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class WeatherDataTransformer:
    """Class for transforming and enriching weather data"""
    
    def __init__(self):
        pass
    
    def transform_to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Transform list of weather data dictionaries to pandas DataFrame
        
        Args:
            data: List of weather data dictionaries
            
        Returns:
            Pandas DataFrame
        """
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Convert timestamp columns to datetime
        timestamp_columns = ["timestamp", "api_timestamp", "forecast_time", "sunrise", "sunset"]
        for col in timestamp_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        # Set timestamp as index if available
        if "timestamp" in df.columns:
            df.set_index("timestamp", inplace=True)
        
        return df
    
    def add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived features to weather data
        
        Args:
            df: DataFrame containing weather data
            
        Returns:
            DataFrame with additional derived features
        """
        df_transformed = df.copy()
        
        # Temperature-based features
        if "temperature" in df.columns and "humidity" in df.columns:
            # Heat index calculation (simplified)
            df_transformed["heat_index"] = self._calculate_heat_index(
                df["temperature"], df["humidity"]
            )
        
        if "feels_like" in df.columns and "temperature" in df.columns:
            # Temperature difference
            df_transformed["temp_feels_like_diff"] = df["feels_like"] - df["temperature"]
        
        if "temperature_max" in df.columns and "temperature_min" in df.columns:
            # Daily temperature range
            df_transformed["temp_range"] = df["temperature_max"] - df["temperature_min"]
        
        # Wind-based features
        if "wind_speed" in df.columns and "wind_direction" in df.columns:
            # Wind components
            wind_rad = np.radians(df["wind_direction"])
            df_transformed["wind_u"] = df["wind_speed"] * np.sin(wind_rad)  # East-west component
            df_transformed["wind_v"] = df["wind_speed"] * np.cos(wind_rad)  # North-south component
        
        # Pressure trend (requires time-series data)
        if "pressure" in df.columns and len(df) > 1:
            df_transformed["pressure_trend"] = df["pressure"].diff()
        
        # Comfort index
        if all(col in df.columns for col in ["temperature", "humidity", "wind_speed"]):
            df_transformed["comfort_index"] = self._calculate_comfort_index(
                df["temperature"], df["humidity"], df["wind_speed"]
            )
        
        # Time-based features
        if df.index.name == "timestamp" or "timestamp" in df.columns:
            timestamp_col = df.index if df.index.name == "timestamp" else df["timestamp"]
            
            df_transformed["hour"] = timestamp_col.hour
            df_transformed["day_of_week"] = timestamp_col.dayofweek
            df_transformed["month"] = timestamp_col.month
            df_transformed["season"] = self._get_season(timestamp_col.month)
            df_transformed["is_weekend"] = timestamp_col.dayofweek >= 5
        
        # Weather condition categories
        if "weather_main" in df.columns:
            df_transformed["weather_category"] = self._categorize_weather(df["weather_main"])
        
        return df_transformed
    
    def aggregate_data(self, df: pd.DataFrame, frequency: str = "D") -> pd.DataFrame:
        """
        Aggregate weather data by time frequency
        
        Args:
            df: DataFrame containing weather data
            frequency: Pandas frequency string ('H', 'D', 'W', 'M')
            
        Returns:
            Aggregated DataFrame
        """
        if df.empty or df.index.name != "timestamp":
            logger.warning("DataFrame must have timestamp index for aggregation")
            return df
        
        # Define aggregation functions for different columns
        agg_functions = {
            "temperature": ["mean", "min", "max", "std"],
            "feels_like": ["mean", "min", "max"],
            "humidity": ["mean", "min", "max"],
            "pressure": ["mean", "min", "max"],
            "wind_speed": ["mean", "max"],
            "cloudiness": "mean",
            "visibility": "mean"
        }
        
        # Only aggregate columns that exist
        available_agg = {}
        for col, func in agg_functions.items():
            if col in df.columns:
                available_agg[col] = func
        
        if not available_agg:
            logger.warning("No aggregatable columns found")
            return df
        
        # Perform aggregation
        aggregated = df.groupby(pd.Grouper(freq=frequency)).agg(available_agg)
        
        # Flatten column names for multi-level aggregation
        if isinstance(aggregated.columns, pd.MultiIndex):
            aggregated.columns = [f"{col}_{agg}" for col, agg in aggregated.columns]
        
        # Add additional statistics
        if "temperature_mean" in aggregated.columns:
            aggregated["temp_range_daily"] = aggregated.get("temperature_max", 0) - aggregated.get("temperature_min", 0)
        
        return aggregated
    
    def calculate_rolling_statistics(self, df: pd.DataFrame, window: int = 24) -> pd.DataFrame:
        """
        Calculate rolling statistics for weather data
        
        Args:
            df: DataFrame containing weather data
            window: Window size for rolling calculations
            
        Returns:
            DataFrame with rolling statistics
        """
        df_rolling = df.copy()
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col in df.columns:
                df_rolling[f"{col}_rolling_mean"] = df[col].rolling(window=window).mean()
                df_rolling[f"{col}_rolling_std"] = df[col].rolling(window=window).std()
                df_rolling[f"{col}_rolling_min"] = df[col].rolling(window=window).min()
                df_rolling[f"{col}_rolling_max"] = df[col].rolling(window=window).max()
        
        return df_rolling
    
    def _calculate_heat_index(self, temperature: pd.Series, humidity: pd.Series) -> pd.Series:
        """
        Calculate heat index (simplified formula)
        
        Args:
            temperature: Temperature in Celsius
            humidity: Relative humidity percentage
            
        Returns:
            Heat index series
        """
        # Convert to Fahrenheit for heat index calculation
        temp_f = temperature * 9/5 + 32
        
        # Simplified heat index formula
        heat_index_f = (
            -42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
            - 0.22475541 * temp_f * humidity - 6.83783e-3 * temp_f**2
            - 5.481717e-2 * humidity**2 + 1.22874e-3 * temp_f**2 * humidity
            + 8.5282e-4 * temp_f * humidity**2 - 1.99e-6 * temp_f**2 * humidity**2
        )
        
        # Convert back to Celsius
        heat_index_c = (heat_index_f - 32) * 5/9
        
        return heat_index_c
    
    def _calculate_comfort_index(self, temperature: pd.Series, humidity: pd.Series, wind_speed: pd.Series) -> pd.Series:
        """
        Calculate comfort index based on temperature, humidity, and wind
        
        Args:
            temperature: Temperature in Celsius
            humidity: Relative humidity percentage
            wind_speed: Wind speed in m/s
            
        Returns:
            Comfort index series (0-100, higher is more comfortable)
        """
        # Normalize temperature (optimal around 20-25°C)
        temp_comfort = 100 - np.abs(temperature - 22.5) * 4
        temp_comfort = np.clip(temp_comfort, 0, 100)
        
        # Normalize humidity (optimal around 40-60%)
        humidity_comfort = 100 - np.abs(humidity - 50) * 2
        humidity_comfort = np.clip(humidity_comfort, 0, 100)
        
        # Normalize wind speed (optimal around 2-5 m/s)
        wind_comfort = 100 - np.abs(wind_speed - 3.5) * 20
        wind_comfort = np.clip(wind_comfort, 0, 100)
        
        # Weighted average
        comfort_index = (temp_comfort * 0.5 + humidity_comfort * 0.3 + wind_comfort * 0.2)
        
        return comfort_index
    
    def _get_season(self, month: pd.Series) -> pd.Series:
        """
        Get season based on month (Northern hemisphere)
        
        Args:
            month: Month number (1-12)
            
        Returns:
            Season series
        """
        conditions = [
            month.isin([12, 1, 2]),  # Winter
            month.isin([3, 4, 5]),   # Spring
            month.isin([6, 7, 8]),   # Summer
            month.isin([9, 10, 11])  # Autumn
        ]
        choices = ["Winter", "Spring", "Summer", "Autumn"]
        
        return pd.Series(np.select(conditions, choices, default="Unknown"), index=month.index)
    
    def _categorize_weather(self, weather_main: pd.Series) -> pd.Series:
        """
        Categorize weather conditions into broader categories
        
        Args:
            weather_main: Weather main condition
            
        Returns:
            Weather category series
        """
        category_mapping = {
            "Clear": "Clear",
            "Clouds": "Cloudy",
            "Rain": "Precipitation",
            "Drizzle": "Precipitation",
            "Thunderstorm": "Severe",
            "Snow": "Precipitation",
            "Mist": "Atmospheric",
            "Fog": "Atmospheric",
            "Haze": "Atmospheric",
            "Dust": "Atmospheric",
            "Sand": "Atmospheric",
            "Ash": "Atmospheric",
            "Squall": "Severe",
            "Tornado": "Severe"
        }
        
        return weather_main.map(category_mapping).fillna("Other")