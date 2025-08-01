"""
Weather dashboard application using Dash/Plotly
"""
import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import logging

from config.settings import settings
from src.weather_pipeline.database.connection import weather_repository

logger = logging.getLogger(__name__)


class WeatherDashboard:
    """Main dashboard class for weather data visualization"""
    
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[
            'https://codepen.io/chriddyp/pen/bWLwgP.css'
        ])
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Setup the dashboard layout"""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("Weather Data Analysis Dashboard", 
                       style={'textAlign': 'center', 'color': '#2c3e50'}),
                html.P("Real-time weather data monitoring and analysis",
                      style={'textAlign': 'center', 'color': '#7f8c8d'})
            ], style={'padding': '20px'}),
            
            # Control panel
            html.Div([
                html.Div([
                    html.Label("Select City:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='city-dropdown',
                        options=[],
                        value=None,
                        placeholder="Select a city..."
                    )
                ], style={'width': '30%', 'display': 'inline-block', 'margin': '10px'}),
                
                html.Div([
                    html.Label("Date Range:", style={'fontWeight': 'bold'}),
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date=datetime.now() - timedelta(days=7),
                        end_date=datetime.now(),
                        display_format='YYYY-MM-DD'
                    )
                ], style={'width': '30%', 'display': 'inline-block', 'margin': '10px'}),
                
                html.Div([
                    html.Button('Refresh Data', id='refresh-button', 
                               style={'backgroundColor': '#3498db', 'color': 'white',
                                     'border': 'none', 'padding': '10px 20px',
                                     'cursor': 'pointer', 'borderRadius': '5px'})
                ], style={'width': '30%', 'display': 'inline-block', 'margin': '10px',
                         'textAlign': 'center'})
            ], style={'backgroundColor': '#ecf0f1', 'padding': '15px',
                     'borderRadius': '10px', 'margin': '20px'}),
            
            # Key metrics cards
            html.Div(id='metrics-cards', style={'margin': '20px'}),
            
            # Charts section
            html.Div([
                # Temperature trend chart
                html.Div([
                    dcc.Graph(id='temperature-trend')
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                # Weather distribution chart
                html.Div([
                    dcc.Graph(id='weather-distribution')
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            
            html.Div([
                # Humidity and pressure chart
                html.Div([
                    dcc.Graph(id='humidity-pressure')
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                # Wind analysis chart
                html.Div([
                    dcc.Graph(id='wind-analysis')
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            
            # Data table
            html.Div([
                html.H3("Recent Weather Data", style={'color': '#2c3e50'}),
                html.Div(id='data-table')
            ], style={'margin': '20px'}),
            
            # Auto-refresh interval
            dcc.Interval(
                id='interval-component',
                interval=5*60*1000,  # 5 minutes in milliseconds
                n_intervals=0
            )
        ])
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            Output('city-dropdown', 'options'),
            Input('refresh-button', 'n_clicks'),
            Input('interval-component', 'n_intervals')
        )
        def update_city_options(n_clicks, n_intervals):
            """Update available cities in dropdown"""
            try:
                stats = weather_repository.get_database_stats()
                cities = stats.get('unique_cities', [])
                return [{'label': city, 'value': city} for city in cities]
            except Exception as e:
                logger.error(f"Error updating city options: {e}")
                return []
        
        @self.app.callback(
            [Output('metrics-cards', 'children'),
             Output('temperature-trend', 'figure'),
             Output('weather-distribution', 'figure'),
             Output('humidity-pressure', 'figure'),
             Output('wind-analysis', 'figure'),
             Output('data-table', 'children')],
            [Input('city-dropdown', 'value'),
             Input('date-picker-range', 'start_date'),
             Input('date-picker-range', 'end_date'),
             Input('refresh-button', 'n_clicks'),
             Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(city, start_date, end_date, n_clicks, n_intervals):
            """Update all dashboard components"""
            try:
                # Get data
                df = weather_repository.get_weather_data_as_dataframe(
                    city=city, 
                    start_date=start_date, 
                    end_date=end_date,
                    limit=1000
                )
                
                if df.empty:
                    empty_fig = go.Figure()
                    empty_fig.add_annotation(
                        text="No data available for selected filters",
                        xref="paper", yref="paper", x=0.5, y=0.5,
                        showarrow=False
                    )
                    return (
                        html.P("No data available"),
                        empty_fig, empty_fig, empty_fig, empty_fig,
                        html.P("No data to display")
                    )
                
                # Generate components
                metrics = self.create_metrics_cards(df)
                temp_fig = self.create_temperature_trend(df)
                weather_fig = self.create_weather_distribution(df)
                humidity_fig = self.create_humidity_pressure_chart(df)
                wind_fig = self.create_wind_analysis(df)
                table = self.create_data_table(df)
                
                return metrics, temp_fig, weather_fig, humidity_fig, wind_fig, table
                
            except Exception as e:
                logger.error(f"Error updating dashboard: {e}")
                empty_fig = go.Figure()
                return (
                    html.P("Error loading data"),
                    empty_fig, empty_fig, empty_fig, empty_fig,
                    html.P("Error loading data")
                )
    
    def create_metrics_cards(self, df: pd.DataFrame):
        """Create metrics cards showing key statistics"""
        if df.empty:
            return html.P("No data available")
        
        avg_temp = df['temperature'].mean() if 'temperature' in df.columns else 0
        avg_humidity = df['humidity'].mean() if 'humidity' in df.columns else 0
        latest_city = df['city'].iloc[0] if 'city' in df.columns and len(df) > 0 else "N/A"
        data_points = len(df)
        
        cards = html.Div([
            # Average Temperature Card
            html.Div([
                html.H4(f"{avg_temp:.1f}°C", style={'margin': '0', 'color': '#e74c3c'}),
                html.P("Average Temperature", style={'margin': '0', 'color': '#7f8c8d'})
            ], style={
                'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                'width': '22%', 'display': 'inline-block', 'margin': '1%'
            }),
            
            # Average Humidity Card
            html.Div([
                html.H4(f"{avg_humidity:.1f}%", style={'margin': '0', 'color': '#3498db'}),
                html.P("Average Humidity", style={'margin': '0', 'color': '#7f8c8d'})
            ], style={
                'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                'width': '22%', 'display': 'inline-block', 'margin': '1%'
            }),
            
            # Latest City Card
            html.Div([
                html.H4(latest_city, style={'margin': '0', 'color': '#27ae60'}),
                html.P("Latest City", style={'margin': '0', 'color': '#7f8c8d'})
            ], style={
                'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                'width': '22%', 'display': 'inline-block', 'margin': '1%'
            }),
            
            # Data Points Card
            html.Div([
                html.H4(str(data_points), style={'margin': '0', 'color': '#f39c12'}),
                html.P("Data Points", style={'margin': '0', 'color': '#7f8c8d'})
            ], style={
                'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                'width': '22%', 'display': 'inline-block', 'margin': '1%'
            })
        ])
        
        return cards
    
    def create_temperature_trend(self, df: pd.DataFrame):
        """Create temperature trend chart"""
        if df.empty or 'temperature' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No temperature data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        fig = go.Figure()
        
        # Add temperature line
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['temperature'],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=4)
        ))
        
        # Add feels like temperature if available
        if 'feels_like' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['feels_like'],
                mode='lines',
                name='Feels Like',
                line=dict(color='#f39c12', width=1, dash='dash')
            ))
        
        fig.update_layout(
            title="Temperature Trend",
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    def create_weather_distribution(self, df: pd.DataFrame):
        """Create weather condition distribution chart"""
        if df.empty or 'weather_main' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No weather condition data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        weather_counts = df['weather_main'].value_counts()
        
        fig = go.Figure(data=[
            go.Pie(
                labels=weather_counts.index,
                values=weather_counts.values,
                hole=0.3,
                textinfo='label+percent'
            )
        ])
        
        fig.update_layout(
            title="Weather Conditions Distribution",
            template='plotly_white'
        )
        
        return fig
    
    def create_humidity_pressure_chart(self, df: pd.DataFrame):
        """Create humidity and pressure chart"""
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No humidity/pressure data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        fig = go.Figure()
        
        # Add humidity on left y-axis
        if 'humidity' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['humidity'],
                mode='lines',
                name='Humidity (%)',
                line=dict(color='#3498db', width=2),
                yaxis='y'
            ))
        
        # Add pressure on right y-axis
        if 'pressure' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['pressure'],
                mode='lines',
                name='Pressure (hPa)',
                line=dict(color='#9b59b6', width=2),
                yaxis='y2'
            ))
        
        fig.update_layout(
            title="Humidity and Atmospheric Pressure",
            xaxis_title="Time",
            yaxis=dict(title="Humidity (%)", side="left", color="#3498db"),
            yaxis2=dict(title="Pressure (hPa)", side="right", overlaying="y", color="#9b59b6"),
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    def create_wind_analysis(self, df: pd.DataFrame):
        """Create wind speed and direction analysis"""
        if df.empty or 'wind_speed' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No wind data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        fig = go.Figure()
        
        # Wind speed over time
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['wind_speed'],
            mode='lines+markers',
            name='Wind Speed (m/s)',
            line=dict(color='#16a085', width=2),
            marker=dict(size=4)
        ))
        
        fig.update_layout(
            title="Wind Speed Analysis",
            xaxis_title="Time",
            yaxis_title="Wind Speed (m/s)",
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    def create_data_table(self, df: pd.DataFrame):
        """Create data table showing recent records"""
        if df.empty:
            return html.P("No data to display")
        
        # Select relevant columns and limit rows
        display_columns = ['timestamp', 'city', 'temperature', 'humidity', 'pressure', 'weather_main']
        available_columns = [col for col in display_columns if col in df.columns]
        
        if not available_columns:
            return html.P("No relevant columns to display")
        
        display_df = df[available_columns].head(10)
        
        # Create table
        table = html.Table([
            html.Thead([
                html.Tr([html.Th(col.replace('_', ' ').title()) for col in available_columns])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(str(display_df.iloc[i][col])) for col in available_columns
                ]) for i in range(len(display_df))
            ])
        ], style={'width': '100%', 'border': '1px solid #ddd'})
        
        return table
    
    def run(self, host: str = None, port: int = None, debug: bool = False):
        """Run the dashboard application"""
        host = host or settings.app.dashboard_host
        port = port or settings.app.dashboard_port
        debug = debug or settings.app.debug
        
        logger.info(f"Starting weather dashboard at http://{host}:{port}")
        self.app.run_server(host=host, port=port, debug=debug)


# Create dashboard instance
dashboard = WeatherDashboard()


if __name__ == "__main__":
    dashboard.run()