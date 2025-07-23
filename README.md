# Emotion Recognition & Music Recommendation System

This project combines facial emotion recognition with music recommendations and weather integration to create a personalized experience. It uses machine learning to detect emotions from images and provides song recommendations based on the detected emotion or current weather conditions.

## Features

- **Emotion Recognition**: Detects emotions from uploaded images using a trained machine learning model
- **Music Recommendations**: Suggests songs based on detected emotions using Spotify integration
- **Weather-based Recommendations**: Provides song recommendations based on current weather conditions
- **RESTful API**: Built with FastAPI for easy integration and scalability

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sameerpanhwarit/AI-Song-Recommendation
cd Emotion-Recognition
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
Emotion-Recognition/
├── main.py              # FastAPI application and endpoints
├── model_loader.py      # Emotion prediction model loader
├── spotify_client.py    # Spotify API integration
├── weather_client.py    # Weather API integration
├── requirements.txt     # Project dependencies
└── Model/              # Trained emotion recognition model
```

## API Endpoints

### 1. Emotion-based Song Recommendation
- **Endpoint**: `/recommend`
- **Method**: POST
- **Input**: Image file
- **Output**: Recommended songs based on detected emotion

### 2. Weather-based Song Recommendation
- **Endpoint**: `/weather_songs`
- **Method**: POST
- **Input**: None (uses IP-based location)
- **Output**: Recommended songs based on current weather conditions

## Running the Application

1. Start the FastAPI server:
```bash
python main.py
```

2. The server will start at `http://127.0.0.1:8000`

3. Access the API documentation at `http://127.0.0.1:8000/docs`

## Dependencies

The project uses several key libraries:
- FastAPI for the web framework
- TensorFlow for emotion recognition
- OpenCV for image processing
- Requests for API calls
- Python-dotenv for environment variable management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Spotify API for music recommendations
- Weather API for weather data
- TensorFlow and OpenCV communities for their excellent documentation and support
