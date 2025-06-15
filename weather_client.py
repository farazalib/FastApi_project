import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()
        ip = response.json()['ip']
        return ip
    except requests.RequestException:
        return None


def get_city_from_ip(ip: str) -> str:
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        response.raise_for_status()
        data = response.json()
        return data.get("city", "Unknown")
    except requests.RequestException:
        return "Unknown"

def get_weather_for_city(city: str) -> dict:
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return {}

def map_weather_to_emotion(weather_data: dict) -> str:
    if not weather_data or "weather" not in weather_data or not weather_data["weather"]:
        return "neutral"
    
    weather_main = weather_data["weather"][0]["main"].lower()
    
    if weather_main in ["clear", "sunny"]:
        return "happy"
    elif weather_main in ["rain", "drizzle", "thunderstorm"]:
        return "sad"
    elif weather_main in ["clouds", "mist", "fog"]:
        return "calm"
    elif weather_main in ["snow"]:
        return "peaceful"
    else:
        return "neutral"
