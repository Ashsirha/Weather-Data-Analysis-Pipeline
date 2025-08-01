"""
Tests for database module
"""
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.weather_pipeline.database.models import Base, WeatherData, ForecastData, ProcessedWeatherData, WeatherAlert
from src.weather_pipeline.database.connection import DatabaseManager, WeatherDataRepository


class TestDatabaseModels:
    """Test cases for database models"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary in-memory database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        return engine, SessionLocal
    
    def test_weather_data_model(self, temp_db):
        """Test WeatherData model"""
        engine, SessionLocal = temp_db
        
        with SessionLocal() as session:
            weather_data = WeatherData(
                timestamp=datetime.now(),
                city="London",
                country="GB",
                temperature=15.5,
                humidity=72,
                pressure=1013,
                data_source="test"
            )
            
            session.add(weather_data)
            session.commit()
            
            # Query back
            result = session.query(WeatherData).first()
            assert result.city == "London"
            assert result.temperature == 15.5
    
    def test_forecast_data_model(self, temp_db):
        """Test ForecastData model"""
        engine, SessionLocal = temp_db
        
        with SessionLocal() as session:
            forecast_data = ForecastData(
                timestamp=datetime.now(),
                forecast_time=datetime.now() + timedelta(hours=3),
                city="Paris",
                temperature=18.2,
                humidity=65,
                is_forecast=True
            )
            
            session.add(forecast_data)
            session.commit()
            
            result = session.query(ForecastData).first()
            assert result.city == "Paris"
            assert result.is_forecast == True
    
    def test_weather_alert_model(self, temp_db):
        """Test WeatherAlert model"""
        engine, SessionLocal = temp_db
        
        with SessionLocal() as session:
            alert = WeatherAlert(
                alert_type="extreme",
                severity="high",
                title="High Temperature Alert",
                city="Phoenix",
                timestamp=datetime.now(),
                parameter="temperature",
                threshold_value=40.0,
                actual_value=42.5,
                is_active=True
            )
            
            session.add(alert)
            session.commit()
            
            result = session.query(WeatherAlert).first()
            assert result.alert_type == "extreme"
            assert result.severity == "high"
            assert result.is_active == True


class TestDatabaseManager:
    """Test cases for DatabaseManager"""
    
    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization with SQLite"""
        # Use temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
            temp_db_path = temp_file.name
        
        try:
            db_url = f"sqlite:///{temp_db_path}"
            db_manager = DatabaseManager(database_url=db_url)
            
            assert db_manager.engine is not None
            assert db_manager.SessionLocal is not None
            
            # Test connection
            assert db_manager.test_connection() == True
            
        finally:
            # Clean up
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
    
    def test_database_manager_session_context(self):
        """Test database session context manager"""
        db_manager = DatabaseManager(database_url="sqlite:///:memory:")
        
        with db_manager.get_session() as session:
            # Should not raise any exceptions
            result = session.execute("SELECT 1").scalar()
            assert result == 1


class TestWeatherDataRepository:
    """Test cases for WeatherDataRepository"""
    
    @pytest.fixture
    def repository(self):
        """Create repository with in-memory database"""
        db_manager = DatabaseManager(database_url="sqlite:///:memory:")
        return WeatherDataRepository(db_manager)
    
    @pytest.fixture
    def sample_weather_records(self):
        """Sample weather records for testing"""
        return [
            {
                "timestamp": datetime.now(),
                "city": "London",
                "country": "GB",
                "temperature": 15.5,
                "humidity": 72,
                "pressure": 1013,
                "data_source": "test"
            },
            {
                "timestamp": datetime.now(),
                "city": "Paris",
                "country": "FR",
                "temperature": 18.2,
                "humidity": 65,
                "pressure": 1020,
                "data_source": "test"
            }
        ]
    
    @pytest.fixture
    def sample_forecast_records(self):
        """Sample forecast records for testing"""
        return [
            {
                "timestamp": datetime.now(),
                "forecast_time": datetime.now() + timedelta(hours=3),
                "city": "London",
                "temperature": 16.0,
                "humidity": 70,
                "is_forecast": True
            }
        ]
    
    def test_save_weather_data(self, repository, sample_weather_records):
        """Test saving weather data"""
        count = repository.save_weather_data(sample_weather_records)
        
        assert count == 2
        
        # Verify data was saved
        data = repository.get_weather_data(limit=10)
        assert len(data) == 2
    
    def test_save_forecast_data(self, repository, sample_forecast_records):
        """Test saving forecast data"""
        count = repository.save_forecast_data(sample_forecast_records)
        
        assert count == 1
    
    def test_get_weather_data_filtered(self, repository, sample_weather_records):
        """Test getting weather data with filters"""
        # Save data first
        repository.save_weather_data(sample_weather_records)
        
        # Test city filter
        london_data = repository.get_weather_data(city="London")
        assert len(london_data) == 1
        assert london_data[0].city == "London"
        
        # Test limit
        limited_data = repository.get_weather_data(limit=1)
        assert len(limited_data) == 1
    
    def test_get_weather_data_as_dataframe(self, repository, sample_weather_records):
        """Test getting weather data as DataFrame"""
        # Save data first
        repository.save_weather_data(sample_weather_records)
        
        df = repository.get_weather_data_as_dataframe()
        
        assert len(df) == 2
        assert "city" in df.columns
        assert "temperature" in df.columns
    
    def test_get_latest_weather_by_city(self, repository, sample_weather_records):
        """Test getting latest weather by city"""
        # Save data first
        repository.save_weather_data(sample_weather_records)
        
        latest = repository.get_latest_weather_by_city(["London", "Paris"])
        
        assert len(latest) == 2
        cities = [record.city for record in latest]
        assert "London" in cities
        assert "Paris" in cities
    
    def test_delete_old_data(self, repository, sample_weather_records):
        """Test deleting old data"""
        # Modify timestamps to be old
        old_records = sample_weather_records.copy()
        old_timestamp = datetime.now() - timedelta(days=100)
        for record in old_records:
            record["timestamp"] = old_timestamp
        
        # Save old data
        repository.save_weather_data(old_records)
        
        # Delete old data (keep 30 days)
        deleted_count = repository.delete_old_data(days_to_keep=30)
        
        assert deleted_count == 2
        
        # Verify data is gone
        remaining_data = repository.get_weather_data()
        assert len(remaining_data) == 0
    
    def test_get_database_stats(self, repository, sample_weather_records):
        """Test getting database statistics"""
        # Save some data first
        repository.save_weather_data(sample_weather_records)
        
        stats = repository.get_database_stats()
        
        assert "weather_data_count" in stats
        assert "unique_cities" in stats
        assert "cities_count" in stats
        assert stats["weather_data_count"] == 2
        assert stats["cities_count"] == 2
        assert set(stats["unique_cities"]) == {"London", "Paris"}


if __name__ == "__main__":
    pytest.main([__file__])