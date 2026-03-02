#!/usr/bin/env python3
"""
Advanced Weather Dashboard - Python Command Line Version
Features: Current weather, forecasts, air quality, saved locations
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import argparse
import sys
from dataclasses import dataclass, asdict
import math
import random


@dataclass
class Location:
    name: str
    country: str
    lat: float
    lon: float


@dataclass
class CurrentWeather:
    temp: float
    feels_like: float
    condition: str
    description: str
    humidity: int
    wind_speed: float
    wind_direction: str
    visibility: float
    pressure: int
    uv_index: int
    precipitation: float


@dataclass
class HourlyForecast:
    time: str
    temp: float
    condition: str
    precipitation_chance: int


@dataclass
class DailyForecast:
    date: str
    high: float
    low: float
    condition: str
    precipitation_chance: int


@dataclass
class AirQuality:
    aqi: int
    level: str
    pm25: float
    pm10: float
    o3: float
    no2: float


class WeatherApp:
    def __init__(self, api_key: str = None, data_file: str = "weather_data.json"):
        self.api_key = api_key or "demo_key"  # For demo purposes
        self.data_file = data_file
        self.saved_locations: List[Location] = []
        self.is_metric = True
        self.load_settings()
    
    def load_settings(self):
        """Load settings and saved locations."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.saved_locations = [
                        Location(**loc) for loc in data.get('saved_locations', [])
                    ]
                    self.is_metric = data.get('is_metric', True)
                print(f"📍 Loaded {len(self.saved_locations)} saved locations")
            except Exception as e:
                print(f"❌ Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings and locations."""
        try:
            data = {
                'saved_locations': [asdict(loc) for loc in self.saved_locations],
                'is_metric': self.is_metric,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
    
    def get_coordinates(self, city_name: str) -> Optional[Location]:
        """Get coordinates for a city (mock implementation)."""
        # Mock city coordinates for demo
        cities = {
            'new york': Location('New York', 'US', 40.7128, -74.0060),
            'london': Location('London', 'UK', 51.5074, -0.1278),
            'tokyo': Location('Tokyo', 'JP', 35.6762, 139.6503),
            'paris': Location('Paris', 'FR', 48.8566, 2.3522),
            'sydney': Location('Sydney', 'AU', -33.8688, 151.2093),
            'berlin': Location('Berlin', 'DE', 52.5200, 13.4050),
            'moscow': Location('Moscow', 'RU', 55.7558, 37.6176),
            'toronto': Location('Toronto', 'CA', 43.6532, -79.3832),
            'los angeles': Location('Los Angeles', 'US', 34.0522, -118.2437),
            'chicago': Location('Chicago', 'US', 41.8781, -87.6298)
        }
        
        city_key = city_name.lower()
        return cities.get(city_key)
    
    def generate_mock_weather(self, location: Location) -> Tuple[CurrentWeather, List[HourlyForecast], List[DailyForecast], AirQuality]:
        """Generate mock weather data for demonstration."""
        # Base temperature varies by city and season
        base_temps = {
            'New York': 15, 'London': 12, 'Tokyo': 20, 'Paris': 14,
            'Sydney': 22, 'Berlin': 10, 'Moscow': 5, 'Toronto': 8,
            'Los Angeles': 25, 'Chicago': 12
        }
        
        base_temp = base_temps.get(location.name, 15)
        current_temp = base_temp + random.uniform(-5, 5)
        
        conditions = ['sunny', 'partly-cloudy', 'cloudy', 'rainy', 'snowy']
        condition = random.choice(conditions)
        
        # Current weather
        current = CurrentWeather(
            temp=current_temp,
            feels_like=current_temp + random.uniform(-3, 3),
            condition=condition,
            description=self.get_condition_description(condition),
            humidity=random.randint(40, 80),
            wind_speed=random.uniform(5, 25),
            wind_direction=random.choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']),
            visibility=random.uniform(10, 15),
            pressure=random.randint(1000, 1040),
            uv_index=random.randint(0, 10),
            precipitation=random.uniform(0, 5)
        )
        
        # Hourly forecast (next 24 hours)
        hourly = []
        for i in range(24):
            hour_time = datetime.now() + timedelta(hours=i)
            temp_variation = math.sin((i - 6) / 24 * math.pi * 2) * 5
            hourly.append(HourlyForecast(
                time=hour_time.strftime('%H:00'),
                temp=current_temp + temp_variation + random.uniform(-1, 1),
                condition=random.choice(conditions),
                precipitation_chance=random.randint(0, 60)
            ))
        
        # Daily forecast (next 7 days)
        daily = []
        for i in range(7):
            date = datetime.now() + timedelta(days=i)
            day_name = "Today" if i == 0 else ("Tomorrow" if i == 1 else date.strftime('%A'))
            temp_variation = random.uniform(-5, 5)
            daily.append(DailyForecast(
                date=day_name,
                high=current_temp + temp_variation + 3,
                low=current_temp + temp_variation - 5,
                condition=random.choice(conditions),
                precipitation_chance=random.randint(0, 60)
            ))
        
        # Air quality
        aqi_value = random.randint(10, 150)
        air_quality = AirQuality(
            aqi=aqi_value,
            level=self.get_aqi_level(aqi_value),
            pm25=random.uniform(5, 50),
            pm10=random.uniform(10, 80),
            o3=random.uniform(20, 100),
            no2=random.uniform(10, 60)
        )
        
        return current, hourly, daily, air_quality
    
    def get_condition_description(self, condition: str) -> str:
        descriptions = {
            'sunny': 'Clear sky',
            'partly-cloudy': 'Partly cloudy',
            'cloudy': 'Overcast',
            'rainy': 'Light rain',
            'snowy': 'Snow'
        }
        return descriptions.get(condition, 'Unknown')
    
    def get_condition_icon(self, condition: str) -> str:
        icons = {
            'sunny': '☀️',
            'partly-cloudy': '⛅',
            'cloudy': '☁️',
            'rainy': '🌧️',
            'snowy': '❄️'
        }
        return icons.get(condition, '🌤️')
    
    def get_aqi_level(self, aqi: int) -> str:
        if aqi <= 50:
            return 'Good'
        elif aqi <= 100:
            return 'Moderate'
        elif aqi <= 150:
            return 'Unhealthy for Sensitive Groups'
        else:
            return 'Unhealthy'
    
    def get_uv_level(self, uv_index: int) -> str:
        if uv_index <= 2:
            return 'Low'
        elif uv_index <= 5:
            return 'Moderate'
        elif uv_index <= 7:
            return 'High'
        elif uv_index <= 10:
            return 'Very High'
        else:
            return 'Extreme'
    
    def convert_temperature(self, temp: float) -> float:
        """Convert temperature based on unit setting."""
        if self.is_metric:
            return temp
        else:
            return (temp * 9/5) + 32
    
    def get_temp_unit(self) -> str:
        return "°C" if self.is_metric else "°F"
    
    def display_current_weather(self, location: Location, current: CurrentWeather):
        """Display current weather information."""
        temp = self.convert_temperature(current.temp)
        feels_like = self.convert_temperature(current.feels_like)
        unit = self.get_temp_unit()
        
        print(f"\n🌤️  Current Weather for {location.name}, {location.country}")
        print("=" * 60)
        print(f"{self.get_condition_icon(current.condition)} {current.description}")
        print(f"🌡️  Temperature: {temp:.1f}{unit} (feels like {feels_like:.1f}{unit})")
        print(f"💧 Humidity: {current.humidity}%")
        print(f"💨 Wind: {current.wind_speed:.1f} km/h {current.wind_direction}")
        print(f"👁️  Visibility: {current.visibility:.1f} km")
        print(f"🌡️  Pressure: {current.pressure} hPa")
        print(f"☀️ UV Index: {current.uv_index} ({self.get_uv_level(current.uv_index)})")
        print(f"🌧️  Precipitation: {current.precipitation:.1f} mm")
    
    def display_hourly_forecast(self, hourly: List[HourlyForecast]):
        """Display hourly forecast."""
        print(f"\n⏰ 24-Hour Forecast")
        print("=" * 60)
        
        for i, hour in enumerate(hourly[:12]):  # Show first 12 hours
            temp = self.convert_temperature(hour.temp)
            unit = self.get_temp_unit()
            icon = self.get_condition_icon(hour.condition)
            
            print(f"{hour.time}: {icon} {temp:.0f}{unit} ({hour.precipitation_chance}% rain)")
    
    def display_daily_forecast(self, daily: List[DailyForecast]):
        """Display daily forecast."""
        print(f"\n📅 7-Day Forecast")
        print("=" * 60)
        
        for day in daily:
            high = self.convert_temperature(day.high)
            low = self.convert_temperature(day.low)
            unit = self.get_temp_unit()
            icon = self.get_condition_icon(day.condition)
            
            print(f"{day.date:>10}: {icon} H:{high:.0f}{unit} L:{low:.0f}{unit} ({day.precipitation_chance}% rain)")
    
    def display_air_quality(self, air_quality: AirQuality):
        """Display air quality information."""
        print(f"\n🌫️  Air Quality")
        print("=" * 40)
        print(f"AQI: {air_quality.aqi} ({air_quality.level})")
        print(f"PM2.5: {air_quality.pm25:.1f} μg/m³")
        print(f"PM10: {air_quality.pm10:.1f} μg/m³")
        print(f"O₃: {air_quality.o3:.1f} μg/m³")
        print(f"NO₂: {air_quality.no2:.1f} μg/m³")
    
    def get_weather(self, city_name: str, show_details: bool = True):
        """Get and display weather for a city."""
        location = self.get_coordinates(city_name)
        if not location:
            print(f"❌ City '{city_name}' not found. Try: New York, London, Tokyo, Paris, Sydney, Berlin, Moscow")
            return
        
        print(f"🔍 Getting weather for {location.name}...")
        
        try:
            current, hourly, daily, air_quality = self.generate_mock_weather(location)
            
            self.display_current_weather(location, current)
            
            if show_details:
                self.display_hourly_forecast(hourly)
                self.display_daily_forecast(daily)
                self.display_air_quality(air_quality)
            
        except Exception as e:
            print(f"❌ Error getting weather data: {e}")
    
    def add_location(self, city_name: str):
        """Add a location to saved locations."""
        location = self.get_coordinates(city_name)
        if not location:
            print(f"❌ City '{city_name}' not found")
            return
        
        # Check if already saved
        if any(loc.name == location.name for loc in self.saved_locations):
            print(f"📍 {location.name} is already in saved locations")
            return
        
        self.saved_locations.append(location)
        self.save_settings()
        print(f"✅ Added {location.name} to saved locations")
    
    def remove_location(self, city_name: str):
        """Remove a location from saved locations."""
        self.saved_locations = [
            loc for loc in self.saved_locations 
            if loc.name.lower() != city_name.lower()
        ]
        self.save_settings()
        print(f"🗑️ Removed {city_name} from saved locations")
    
    def list_saved_locations(self):
        """List all saved locations."""
        if not self.saved_locations:
            print("📍 No saved locations")
            return
        
        print(f"\n📍 Saved Locations ({len(self.saved_locations)}):")
        print("=" * 40)
        for i, location in enumerate(self.saved_locations, 1):
            print(f"{i}. {location.name}, {location.country}")
    
    def get_saved_weather(self):
        """Get weather for all saved locations."""
        if not self.saved_locations:
            print("📍 No saved locations. Add some with: weather add <city>")
            return
        
        for location in self.saved_locations:
            current, _, _, _ = self.generate_mock_weather(location)
            temp = self.convert_temperature(current.temp)
            unit = self.get_temp_unit()
            icon = self.get_condition_icon(current.condition)
            
            print(f"{icon} {location.name}: {temp:.0f}{unit} - {current.description}")
    
    def toggle_units(self):
        """Toggle between Celsius and Fahrenheit."""
        self.is_metric = not self.is_metric
        self.save_settings()
        unit = "Celsius" if self.is_metric else "Fahrenheit"
        print(f"🌡️ Switched to {unit}")


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(description="Advanced Weather Dashboard")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Get weather
    weather_parser = subparsers.add_parser('get', help='Get weather for a city')
    weather_parser.add_argument('city', help='City name')
    weather_parser.add_argument('--brief', action='store_true', help='Show brief info only')
    
    # Add location
    add_parser = subparsers.add_parser('add', help='Add city to saved locations')
    add_parser.add_argument('city', help='City name')
    
    # Remove location
    remove_parser = subparsers.add_parser('remove', help='Remove city from saved locations')
    remove_parser.add_argument('city', help='City name')
    
    # List saved locations
    subparsers.add_parser('locations', help='List saved locations')
    
    # Get weather for saved locations
    subparsers.add_parser('saved', help='Get weather for all saved locations')
    
    # Toggle units
    subparsers.add_parser('units', help='Toggle between Celsius and Fahrenheit')
    
    return parser


def main():
    """Main application entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    app = WeatherApp()
    
    try:
        if args.command == 'get':
            app.get_weather(args.city, show_details=not args.brief)
        
        elif args.command == 'add':
            app.add_location(args.city)
        
        elif args.command == 'remove':
            app.remove_location(args.city)
        
        elif args.command == 'locations':
            app.list_saved_locations()
        
        elif args.command == 'saved':
            app.get_saved_weather()
        
        elif args.command == 'units':
            app.toggle_units()
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()