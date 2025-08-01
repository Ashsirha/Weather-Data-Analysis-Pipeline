"""
Application settings and configuration management
"""
import os
from typing import Optional
from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    
    db_type: str = Field(default="sqlite", description="Database type (sqlite, postgresql)")
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="weather_data", description="Database name")
    db_user: Optional[str] = Field(default=None, description="Database username")
    db_password: Optional[str] = Field(default=None, description="Database password")
    db_url: Optional[str] = Field(default=None, description="Complete database URL")
    
    class Config:
        env_prefix = "DB_"


class WeatherAPISettings(BaseSettings):
    """Weather API configuration settings"""
    
    api_key: Optional[str] = Field(default=None, description="Weather API key")
    api_provider: str = Field(default="openweathermap", description="Weather API provider")
    base_url: str = Field(default="https://api.openweathermap.org/data/2.5", description="API base URL")
    rate_limit: int = Field(default=60, description="API calls per minute")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    class Config:
        env_prefix = "WEATHER_API_"


class AppSettings(BaseSettings):
    """Application configuration settings"""
    
    app_name: str = Field(default="Weather Data Analysis Pipeline", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    data_retention_days: int = Field(default=90, description="Data retention period in days")
    
    # Data ingestion settings
    ingestion_interval_minutes: int = Field(default=60, description="Data ingestion interval in minutes")
    batch_size: int = Field(default=100, description="Batch size for data processing")
    
    # Dashboard settings
    dashboard_host: str = Field(default="0.0.0.0", description="Dashboard host")
    dashboard_port: int = Field(default=8050, description="Dashboard port")
    
    class Config:
        env_prefix = "APP_"


class Settings:
    """Main settings class that combines all configuration"""
    
    def __init__(self):
        self.database = DatabaseSettings()
        self.weather_api = WeatherAPISettings()
        self.app = AppSettings()
    
    @property
    def database_url(self) -> str:
        """Generate database URL from settings"""
        if self.database.db_url:
            return self.database.db_url
        
        if self.database.db_type == "sqlite":
            return f"sqlite:///data/{self.database.db_name}.db"
        elif self.database.db_type == "postgresql":
            user_pass = ""
            if self.database.db_user and self.database.db_password:
                user_pass = f"{self.database.db_user}:{self.database.db_password}@"
            return f"postgresql://{user_pass}{self.database.db_host}:{self.database.db_port}/{self.database.db_name}"
        else:
            raise ValueError(f"Unsupported database type: {self.database.db_type}")


# Global settings instance
settings = Settings()