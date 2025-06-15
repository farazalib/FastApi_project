import numpy as np
from tensorflow.keras.models import load_model
from PIL import Image

model = load_model("./Model/FER_DATA.keras")

emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

def predict_emotion(image_path: str) -> str:
    img = Image.open(image_path).convert('L').resize((48, 48))
    img_array = np.array(img) / 255.0
    img_array = img_array.reshape(1, 48, 48, 1)

    predictions = model.predict(img_array)
    emotion_index = np.argmax(predictions)
    return emotion_labels[emotion_index]
