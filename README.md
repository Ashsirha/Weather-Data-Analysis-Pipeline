# Weather Data Analysis Pipeline

A comprehensive pipeline for ingesting, processing, storing, and analyzing weather data from public APIs. This project provides real-time weather data collection, automated data cleaning and transformation, SQL storage, and an interactive dashboard for visualization and analysis.

## Features

- **Data Ingestion**: Automated collection of weather data from OpenWeatherMap API
- **Data Processing**: Robust data cleaning, validation, and transformation pipeline
- **Database Storage**: Flexible storage in SQLite or PostgreSQL with optimized schemas
- **Interactive Dashboard**: Real-time web dashboard for data visualization and analysis
- **Anomaly Detection**: Built-in algorithms to detect weather anomalies and extremes
- **Scalable Architecture**: Containerized deployment with Docker and Docker Compose
- **Comprehensive Testing**: Full test suite with pytest
- **CLI Interface**: Command-line tools for data management and operations

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Weather APIs  │    │  Data Pipeline  │    │    Database     │
│                 │────│                 │────│                 │
│ • OpenWeatherMap│    │ • Data Ingestion│    │ • SQLite/       │
│ • Other APIs    │    │ • Data Cleaning │    │   PostgreSQL    │
└─────────────────┘    │ • Transformation│    │ • Weather Data  │
                       │ • Validation    │    │ • Forecasts     │
                       └─────────────────┘    │ • Processed Data│
                                              └─────────────────┘
                                                       │
                       ┌─────────────────┐           │
                       │   Dashboard     │───────────┘
                       │                 │
                       │ • Real-time viz │
                       │ • Trend analysis│
                       │ • Anomaly alerts│
                       └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenWeatherMap API key (free at [openweathermap.org](https://openweathermap.org/api))
- Docker and Docker Compose (optional, for containerized deployment)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Ashsirha/Weather-Data-Analysis-Pipeline.git
   cd Weather-Data-Analysis-Pipeline
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install the package**:
   ```bash
   pip install -e .
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env file and add your OpenWeatherMap API key
   ```

### Usage

#### Command Line Interface

The pipeline provides a comprehensive CLI for all operations:

```bash
# Collect weather data for default cities
python -m src.weather_pipeline.cli collect

# Collect data for specific cities
python -m src.weather_pipeline.cli collect --cities London Paris Tokyo

# Run the interactive dashboard
python -m src.weather_pipeline.cli dashboard

# Start automated data collection scheduler
python -m src.weather_pipeline.cli schedule

# Show database statistics
python -m src.weather_pipeline.cli stats

# Test API and database connections
python -m src.weather_pipeline.cli test all

# Clean up old data
python -m src.weather_pipeline.cli cleanup --days 30
```

#### Dashboard

Access the interactive dashboard at `http://localhost:8050` after running:

```bash
python -m src.weather_pipeline.cli dashboard
```

The dashboard provides:
- Real-time weather data visualization
- Temperature trends and forecasts
- Weather condition distributions
- Humidity and pressure analysis
- Wind speed and direction charts
- Data filtering by city and date range

#### Docker Deployment

For production deployment with PostgreSQL:

```bash
# Set your API key in environment
export WEATHER_API_KEY=your_api_key_here

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Project Structure

```
Weather-Data-Analysis-Pipeline/
├── src/weather_pipeline/          # Main application code
│   ├── data_ingestion/            # Weather API clients and data collection
│   ├── data_processing/           # Data cleaning and transformation
│   ├── database/                  # Database models and connections
│   ├── dashboard/                 # Web dashboard application
│   └── cli.py                     # Command-line interface
├── config/                        # Configuration management
├── tests/                         # Test suite
├── data/                          # Data storage directory
├── logs/                          # Application logs
├── requirements.txt               # Python dependencies
├── setup.py                       # Package installation
├── Dockerfile                     # Container image definition
├── docker-compose.yml             # Multi-service deployment
└── .env.example                   # Environment configuration template
```

## Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and customize:

### Required Settings

- `WEATHER_API_KEY`: Your OpenWeatherMap API key

### Optional Settings

- `DB_TYPE`: Database type (`sqlite` or `postgresql`)
- `DB_HOST`: Database host (for PostgreSQL)
- `DB_NAME`: Database name
- `APP_LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `APP_INGESTION_INTERVAL_MINUTES`: Data collection interval
- `APP_DASHBOARD_PORT`: Dashboard port number

## Data Sources

### Weather APIs Supported

- **OpenWeatherMap** (default): Current weather and forecasts
- Extensible architecture for additional weather APIs

### Data Points Collected

- Temperature (current, feels like, min/max)
- Atmospheric pressure
- Humidity percentage
- Wind speed and direction
- Cloud coverage
- Visibility
- Weather conditions
- Sunrise/sunset times
- Location coordinates

## Database Schema

### Weather Data Table
- Timestamp and location information
- All weather parameters
- Data source and quality flags
- Indexed for efficient querying

### Forecast Data Table
- Future weather predictions
- Forecast confidence intervals
- Multiple time horizons

### Processed Data Table
- Aggregated statistics (hourly, daily, weekly)
- Derived features and indicators
- Trend calculations

### Alerts Table
- Anomaly detection results
- Extreme weather warnings
- Alert severity levels

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/weather_pipeline

# Run specific test modules
pytest tests/test_data_ingestion.py
pytest tests/test_data_processing.py
pytest tests/test_database.py
```

## Development

### Setting up development environment

```bash
# Clone and setup
git clone https://github.com/Ashsirha/Weather-Data-Analysis-Pipeline.git
cd Weather-Data-Analysis-Pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run linting
black src/ tests/
flake8 src/ tests/
isort src/ tests/
```

### Adding new weather APIs

1. Create a new API client in `src/weather_pipeline/data_ingestion/`
2. Implement the standardized data format
3. Add configuration options in `config/settings.py`
4. Update tests and documentation

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the test suite
5. Submit a pull request

## Monitoring and Maintenance

### Health Checks

```bash
# Test all connections
python -m src.weather_pipeline.cli test all

# Check database statistics
python -m src.weather_pipeline.cli stats

# View application logs
tail -f logs/weather_pipeline.log
```

### Data Retention

Configure automatic cleanup of old data:

```bash
# Clean data older than 90 days (default)
python -m src.weather_pipeline.cli cleanup

# Custom retention period
python -m src.weather_pipeline.cli cleanup --days 30
```

## Troubleshooting

### Common Issues

1. **API Key Issues**:
   - Verify your OpenWeatherMap API key is valid
   - Check API rate limits and quotas

2. **Database Connection**:
   - Ensure database server is running (for PostgreSQL)
   - Check connection parameters in `.env`

3. **Dashboard Not Loading**:
   - Verify port 8050 is available
   - Check firewall settings
   - Review dashboard logs

### Logging

Application logs are written to `logs/weather_pipeline.log`. Adjust log level in configuration:

```bash
# Debug mode for troubleshooting
export APP_LOG_LEVEL=DEBUG
```

## Performance Optimization

### Database Optimization

- Indexes are automatically created for common queries
- Consider partitioning for large datasets
- Regular VACUUM and ANALYZE for PostgreSQL

### API Rate Limiting

- Built-in rate limiting respects API quotas
- Configurable request intervals
- Automatic retry with exponential backoff

### Memory Management

- Batch processing for large datasets
- Configurable batch sizes
- Streaming for very large data exports

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenWeatherMap](https://openweathermap.org/) for weather data API
- [Plotly Dash](https://dash.plotly.com/) for dashboard framework
- [SQLAlchemy](https://sqlalchemy.org/) for database ORM
- [Pandas](https://pandas.pydata.org/) for data processing

## Support

For questions, issues, or contributions:

- Create an issue on GitHub
- Check the troubleshooting section
- Review the test suite for usage examples

---

**Note**: This pipeline is designed for educational and research purposes. For production weather applications, consider enterprise weather data providers and additional data validation measures.
