"""
Database connection and operations
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import logging
import pandas as pd

from config.settings import settings
from .models import Base, WeatherData, ForecastData, ProcessedWeatherData, WeatherAlert

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            self.engine = create_engine(
                self.database_url,
                echo=settings.app.debug,
                pool_pre_ping=True
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables if they don't exist
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


class WeatherDataRepository:
    """Repository for weather data operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_weather_data(self, weather_records: List[Dict[str, Any]]) -> int:
        """
        Save weather data records to database
        
        Args:
            weather_records: List of weather data dictionaries
            
        Returns:
            Number of records saved
        """
        if not weather_records:
            return 0
        
        saved_count = 0
        
        with self.db_manager.get_session() as session:
            for record in weather_records:
                try:
                    weather_data = WeatherData(**record)
                    session.add(weather_data)
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"Failed to save weather record: {e}")
            
            session.commit()
        
        logger.info(f"Saved {saved_count} weather records to database")
        return saved_count
    
    def save_forecast_data(self, forecast_records: List[Dict[str, Any]]) -> int:
        """
        Save forecast data records to database
        
        Args:
            forecast_records: List of forecast data dictionaries
            
        Returns:
            Number of records saved
        """
        if not forecast_records:
            return 0
        
        saved_count = 0
        
        with self.db_manager.get_session() as session:
            for record in forecast_records:
                try:
                    forecast_data = ForecastData(**record)
                    session.add(forecast_data)
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"Failed to save forecast record: {e}")
            
            session.commit()
        
        logger.info(f"Saved {saved_count} forecast records to database")
        return saved_count
    
    def get_weather_data(self, city: Optional[str] = None, 
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        limit: int = 1000) -> List[WeatherData]:
        """
        Retrieve weather data from database
        
        Args:
            city: Filter by city name
            start_date: Start date for filtering (ISO format)
            end_date: End date for filtering (ISO format)
            limit: Maximum number of records to return
            
        Returns:
            List of WeatherData objects
        """
        with self.db_manager.get_session() as session:
            query = session.query(WeatherData)
            
            if city:
                query = query.filter(WeatherData.city.ilike(f"%{city}%"))
            
            if start_date:
                query = query.filter(WeatherData.timestamp >= start_date)
            
            if end_date:
                query = query.filter(WeatherData.timestamp <= end_date)
            
            query = query.order_by(WeatherData.timestamp.desc()).limit(limit)
            
            return query.all()
    
    def get_weather_data_as_dataframe(self, city: Optional[str] = None,
                                    start_date: Optional[str] = None,
                                    end_date: Optional[str] = None,
                                    limit: int = 1000) -> pd.DataFrame:
        """
        Retrieve weather data as pandas DataFrame
        
        Args:
            city: Filter by city name
            start_date: Start date for filtering (ISO format)
            end_date: End date for filtering (ISO format)
            limit: Maximum number of records to return
            
        Returns:
            Pandas DataFrame
        """
        query = f"""
        SELECT * FROM weather_data
        WHERE 1=1
        """
        
        params = {}
        
        if city:
            query += " AND city ILIKE :city"
            params["city"] = f"%{city}%"
        
        if start_date:
            query += " AND timestamp >= :start_date"
            params["start_date"] = start_date
        
        if end_date:
            query += " AND timestamp <= :end_date"
            params["end_date"] = end_date
        
        query += " ORDER BY timestamp DESC LIMIT :limit"
        params["limit"] = limit
        
        df = pd.read_sql_query(query, self.db_manager.engine, params=params)
        
        # Convert timestamp columns to datetime
        timestamp_cols = ["timestamp", "api_timestamp", "sunrise", "sunset", "created_at"]
        for col in timestamp_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        return df
    
    def get_latest_weather_by_city(self, cities: List[str]) -> List[WeatherData]:
        """
        Get latest weather data for specified cities
        
        Args:
            cities: List of city names
            
        Returns:
            List of latest WeatherData objects for each city
        """
        with self.db_manager.get_session() as session:
            latest_weather = []
            
            for city in cities:
                latest = session.query(WeatherData)\
                    .filter(WeatherData.city.ilike(f"%{city}%"))\
                    .order_by(WeatherData.timestamp.desc())\
                    .first()
                
                if latest:
                    latest_weather.append(latest)
            
            return latest_weather
    
    def delete_old_data(self, days_to_keep: int = 90) -> int:
        """
        Delete old weather data beyond retention period
        
        Args:
            days_to_keep: Number of days of data to retain
            
        Returns:
            Number of records deleted
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with self.db_manager.get_session() as session:
            # Delete old weather data
            deleted_weather = session.query(WeatherData)\
                .filter(WeatherData.timestamp < cutoff_date)\
                .delete()
            
            # Delete old forecast data
            deleted_forecast = session.query(ForecastData)\
                .filter(ForecastData.timestamp < cutoff_date)\
                .delete()
            
            session.commit()
            
            total_deleted = deleted_weather + deleted_forecast
            logger.info(f"Deleted {total_deleted} old records (older than {cutoff_date})")
            
            return total_deleted
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary containing database statistics
        """
        with self.db_manager.get_session() as session:
            stats = {}
            
            # Count records in each table
            stats["weather_data_count"] = session.query(WeatherData).count()
            stats["forecast_data_count"] = session.query(ForecastData).count()
            stats["processed_data_count"] = session.query(ProcessedWeatherData).count()
            stats["alerts_count"] = session.query(WeatherAlert).count()
            
            # Get date ranges
            if stats["weather_data_count"] > 0:
                oldest_weather = session.query(WeatherData.timestamp)\
                    .order_by(WeatherData.timestamp.asc()).first()
                newest_weather = session.query(WeatherData.timestamp)\
                    .order_by(WeatherData.timestamp.desc()).first()
                
                stats["oldest_weather_data"] = oldest_weather[0] if oldest_weather else None
                stats["newest_weather_data"] = newest_weather[0] if newest_weather else None
            
            # Get unique cities
            cities_result = session.query(WeatherData.city).distinct().all()
            stats["unique_cities"] = [city[0] for city in cities_result]
            stats["cities_count"] = len(stats["unique_cities"])
            
            return stats


# Global database manager instance
db_manager = DatabaseManager()
weather_repository = WeatherDataRepository(db_manager)