"""
Command line interface for the Weather Data Analysis Pipeline
"""
import argparse
import logging
import sys
from datetime import datetime
import schedule
import time

from config.settings import settings
from src.weather_pipeline.data_ingestion.weather_api import WeatherDataCollector
from src.weather_pipeline.data_processing.cleaner import WeatherDataCleaner
from src.weather_pipeline.data_processing.transformer import WeatherDataTransformer
from src.weather_pipeline.database.connection import weather_repository
from src.weather_pipeline.dashboard.app import dashboard

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.app.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/weather_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def collect_weather_data(cities=None):
    """Collect weather data for specified cities"""
    logger.info("Starting weather data collection")
    
    try:
        collector = WeatherDataCollector()
        cleaner = WeatherDataCleaner()
        transformer = WeatherDataTransformer()
        
        # Collect current weather data
        raw_data = collector.collect_current_weather_batch(cities)
        if not raw_data:
            logger.warning("No weather data collected")
            return
        
        # Clean the data
        cleaned_data = cleaner.clean_weather_data(raw_data)
        if not cleaned_data:
            logger.warning("No data remaining after cleaning")
            return
        
        # Save to database
        saved_count = weather_repository.save_weather_data(cleaned_data)
        logger.info(f"Successfully saved {saved_count} weather records")
        
        # Collect forecast data
        forecast_data = collector.collect_forecast_batch(cities)
        if forecast_data:
            cleaned_forecast = cleaner.clean_weather_data(forecast_data)
            saved_forecast_count = weather_repository.save_forecast_data(cleaned_forecast)
            logger.info(f"Successfully saved {saved_forecast_count} forecast records")
        
    except Exception as e:
        logger.error(f"Error during weather data collection: {e}")
        raise


def run_dashboard():
    """Run the weather dashboard"""
    logger.info("Starting weather dashboard")
    try:
        dashboard.run()
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        raise


def run_scheduler():
    """Run the data collection scheduler"""
    logger.info("Starting weather data collection scheduler")
    
    # Schedule data collection
    interval = settings.app.ingestion_interval_minutes
    schedule.every(interval).minutes.do(collect_weather_data)
    
    logger.info(f"Scheduled data collection every {interval} minutes")
    
    # Run initial collection
    collect_weather_data()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Error in scheduler: {e}")
        raise


def show_stats():
    """Show database statistics"""
    try:
        stats = weather_repository.get_database_stats()
        
        print("\n=== Weather Database Statistics ===")
        print(f"Weather Data Records: {stats.get('weather_data_count', 0)}")
        print(f"Forecast Data Records: {stats.get('forecast_data_count', 0)}")
        print(f"Processed Data Records: {stats.get('processed_data_count', 0)}")
        print(f"Alerts Count: {stats.get('alerts_count', 0)}")
        print(f"Unique Cities: {stats.get('cities_count', 0)}")
        
        if stats.get('unique_cities'):
            print(f"Cities: {', '.join(stats['unique_cities'])}")
        
        if stats.get('oldest_weather_data'):
            print(f"Oldest Data: {stats['oldest_weather_data']}")
        
        if stats.get('newest_weather_data'):
            print(f"Newest Data: {stats['newest_weather_data']}")
        
        print("=" * 35)
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise


def cleanup_old_data():
    """Clean up old data beyond retention period"""
    try:
        retention_days = settings.app.data_retention_days
        deleted_count = weather_repository.delete_old_data(retention_days)
        logger.info(f"Cleaned up {deleted_count} old records (older than {retention_days} days)")
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        raise


def test_api_connection():
    """Test weather API connection"""
    try:
        from src.weather_pipeline.data_ingestion.weather_api import WeatherAPIClient
        
        client = WeatherAPIClient()
        data = client.get_current_weather("London", "GB")
        
        print("\n=== API Connection Test ===")
        print("✓ Successfully connected to weather API")
        print(f"✓ Retrieved data for {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}")
        print(f"✓ Temperature: {data.get('temperature', 'N/A')}°C")
        print(f"✓ Weather: {data.get('weather_description', 'N/A')}")
        print("=" * 27)
        
    except Exception as e:
        print(f"\n✗ API connection test failed: {e}")
        logger.error(f"API connection test failed: {e}")


def test_database_connection():
    """Test database connection"""
    try:
        from src.weather_pipeline.database.connection import db_manager
        
        success = db_manager.test_connection()
        
        print("\n=== Database Connection Test ===")
        if success:
            print("✓ Successfully connected to database")
        else:
            print("✗ Failed to connect to database")
        print("=" * 32)
        
    except Exception as e:
        print(f"\n✗ Database connection test failed: {e}")
        logger.error(f"Database connection test failed: {e}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Weather Data Analysis Pipeline")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Collect data command
    collect_parser = subparsers.add_parser('collect', help='Collect weather data')
    collect_parser.add_argument('--cities', nargs='+', help='Cities to collect data for')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Run the dashboard')
    dashboard_parser.add_argument('--host', default=None, help='Dashboard host')
    dashboard_parser.add_argument('--port', type=int, default=None, help='Dashboard port')
    dashboard_parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser('schedule', help='Run the data collection scheduler')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', type=int, default=None, 
                               help='Number of days to retain (default from config)')
    
    # Test commands
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_subparsers = test_parser.add_subparsers(dest='test_type', help='Test types')
    test_subparsers.add_parser('api', help='Test API connection')
    test_subparsers.add_parser('db', help='Test database connection')
    test_subparsers.add_parser('all', help='Test all connections')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'collect':
            cities = None
            if args.cities:
                cities = [(city, None) for city in args.cities]  # Format for collector
            collect_weather_data(cities)
        
        elif args.command == 'dashboard':
            dashboard.run(host=args.host, port=args.port, debug=args.debug)
        
        elif args.command == 'schedule':
            run_scheduler()
        
        elif args.command == 'stats':
            show_stats()
        
        elif args.command == 'cleanup':
            if args.days:
                # Temporarily override settings
                original_retention = settings.app.data_retention_days
                settings.app.data_retention_days = args.days
                cleanup_old_data()
                settings.app.data_retention_days = original_retention
            else:
                cleanup_old_data()
        
        elif args.command == 'test':
            if args.test_type == 'api':
                test_api_connection()
            elif args.test_type == 'db':
                test_database_connection()
            elif args.test_type == 'all':
                test_api_connection()
                test_database_connection()
            else:
                test_parser.print_help()
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()