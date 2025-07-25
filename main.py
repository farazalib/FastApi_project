from fastapi import FastAPI, File, UploadFile, Query, Request
import shutil
from model_loader import predict_emotion
from spotify_client import get_song_by_emotion
from weather_client import get_city_from_ip, map_weather_to_emotion, get_weather_for_city, get_public_ip
import uvicorn
app = FastAPI()

@app.post("/recommend")
async def recommend_song(file: UploadFile = File(...)):
    file_location = f"temp_{file.filename}"
    
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    emotion = predict_emotion(file_location)
    result = get_song_by_emotion(emotion)

    return result



@app.post("/weather_songs")
async def weather_songs(request: Request):
    ip = get_public_ip()
    city = get_city_from_ip(ip)
    weather = get_weather_for_city(city)
    emotion = map_weather_to_emotion(weather)
    songs = get_song_by_emotion(emotion)
    
    return {
        "city": city,
        "weather": weather.get("weather", [{}])[0].get("description", "No description"),
        "emotion": emotion,
        "songs": songs,
    }

if __name__ == "__main__":
    
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)