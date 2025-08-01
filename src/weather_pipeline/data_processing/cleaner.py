"""
Data cleaning utilities for weather data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class WeatherDataCleaner:
    """Class for cleaning and validating weather data"""
    
    def __init__(self):
        # Define reasonable ranges for weather parameters
        self.validation_ranges = {
            "temperature": (-50, 60),  # Celsius
            "feels_like": (-60, 70),
            "temperature_min": (-60, 60),
            "temperature_max": (-50, 70),
            "pressure": (800, 1200),  # hPa
            "humidity": (0, 100),  # Percentage
            "wind_speed": (0, 200),  # m/s (extreme values for hurricanes)
            "wind_direction": (0, 360),  # Degrees
            "cloudiness": (0, 100),  # Percentage
            "visibility": (0, 50000),  # Meters
            "precipitation_probability": (0, 100)  # Percentage
        }
    
    def clean_weather_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Clean a list of weather data records
        
        Args:
            data: List of weather data dictionaries
            
        Returns:
            List of cleaned weather data dictionaries
        """
        cleaned_data = []
        
        for record in data:
            try:
                cleaned_record = self._clean_single_record(record)
                if cleaned_record:
                    cleaned_data.append(cleaned_record)
            except Exception as e:
                logger.warning(f"Failed to clean weather record: {e}")
        
        logger.info(f"Cleaned {len(cleaned_data)} out of {len(data)} records")
        return cleaned_data
    
    def _clean_single_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean a single weather data record
        
        Args:
            record: Weather data dictionary
            
        Returns:
            Cleaned weather data dictionary or None if invalid
        """
        cleaned = record.copy()
        
        # Validate required fields
        required_fields = ["timestamp", "city", "temperature", "humidity"]
        for field in required_fields:
            if field not in cleaned or cleaned[field] is None:
                logger.warning(f"Missing required field: {field}")
                return None
        
        # Clean and validate numeric fields
        for field, (min_val, max_val) in self.validation_ranges.items():
            if field in cleaned and cleaned[field] is not None:
                try:
                    value = float(cleaned[field])
                    if not (min_val <= value <= max_val):
                        logger.warning(f"Invalid {field} value: {value} (expected {min_val}-{max_val})")
                        cleaned[field] = None
                    else:
                        cleaned[field] = value
                except (ValueError, TypeError):
                    logger.warning(f"Invalid {field} format: {cleaned[field]}")
                    cleaned[field] = None
        
        # Clean string fields
        string_fields = ["city", "country", "weather_main", "weather_description"]
        for field in string_fields:
            if field in cleaned and cleaned[field] is not None:
                cleaned[field] = str(cleaned[field]).strip()
        
        # Validate and standardize timestamps
        timestamp_fields = ["timestamp", "api_timestamp", "forecast_time", "sunrise", "sunset"]
        for field in timestamp_fields:
            if field in cleaned and cleaned[field] is not None:
                if not isinstance(cleaned[field], datetime):
                    try:
                        if isinstance(cleaned[field], str):
                            cleaned[field] = pd.to_datetime(cleaned[field])
                        elif isinstance(cleaned[field], (int, float)):
                            cleaned[field] = datetime.fromtimestamp(cleaned[field])
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid {field} format: {cleaned[field]}")
                        cleaned[field] = None
        
        # Validate coordinate ranges
        if "latitude" in cleaned and cleaned["latitude"] is not None:
            lat = cleaned["latitude"]
            if not (-90 <= lat <= 90):
                logger.warning(f"Invalid latitude: {lat}")
                cleaned["latitude"] = None
        
        if "longitude" in cleaned and cleaned["longitude"] is not None:
            lon = cleaned["longitude"]
            if not (-180 <= lon <= 180):
                logger.warning(f"Invalid longitude: {lon}")
                cleaned["longitude"] = None
        
        return cleaned
    
    def detect_outliers(self, df: pd.DataFrame, column: str, method: str = "iqr") -> pd.Series:
        """
        Detect outliers in a specific column
        
        Args:
            df: DataFrame containing weather data
            column: Column name to check for outliers
            method: Method for outlier detection ('iqr' or 'zscore')
            
        Returns:
            Boolean series indicating outliers
        """
        if column not in df.columns or df[column].isnull().all():
            return pd.Series([False] * len(df), index=df.index)
        
        if method == "iqr":
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return (df[column] < lower_bound) | (df[column] > upper_bound)
        
        elif method == "zscore":
            z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
            return z_scores > 3
        
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
    
    def handle_missing_values(self, df: pd.DataFrame, strategy: str = "interpolate") -> pd.DataFrame:
        """
        Handle missing values in weather data
        
        Args:
            df: DataFrame containing weather data
            strategy: Strategy for handling missing values
                     ('drop', 'interpolate', 'forward_fill', 'backward_fill')
            
        Returns:
            DataFrame with missing values handled
        """
        df_cleaned = df.copy()
        
        if strategy == "drop":
            df_cleaned = df_cleaned.dropna()
        
        elif strategy == "interpolate":
            # Interpolate numeric columns
            numeric_columns = df_cleaned.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if col in df_cleaned.columns:
                    df_cleaned[col] = df_cleaned[col].interpolate(method="linear")
        
        elif strategy == "forward_fill":
            df_cleaned = df_cleaned.fillna(method="ffill")
        
        elif strategy == "backward_fill":
            df_cleaned = df_cleaned.fillna(method="bfill")
        
        else:
            raise ValueError(f"Unknown missing value strategy: {strategy}")
        
        return df_cleaned
    
    def remove_duplicates(self, df: pd.DataFrame, subset: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Remove duplicate records from weather data
        
        Args:
            df: DataFrame containing weather data
            subset: Columns to consider for duplicate detection
            
        Returns:
            DataFrame with duplicates removed
        """
        if subset is None:
            subset = ["city", "timestamp", "temperature", "humidity"]
        
        # Only use columns that exist in the DataFrame
        subset = [col for col in subset if col in df.columns]
        
        if not subset:
            logger.warning("No valid columns for duplicate detection")
            return df
        
        initial_count = len(df)
        df_deduplicated = df.drop_duplicates(subset=subset, keep="first")
        final_count = len(df_deduplicated)
        
        if initial_count > final_count:
            logger.info(f"Removed {initial_count - final_count} duplicate records")
        
        return df_deduplicated