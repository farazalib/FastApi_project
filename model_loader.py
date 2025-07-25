<<<<<<< HEAD
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image

model = tf.keras.models.load_model("./Model/FER_DATA.keras")

emotion_labels = ['Angry', 'Happy', 'Sad',  'Neutral']

def predict_emotion(image_path: str) -> str:
    img = Image.open(image_path).convert('L').resize((48, 48))
    img_array = np.array(img) / 255.0
    img_array = img_array.reshape(1, 48, 48, 1)

    predictions = model.predict(img_array)
    emotion_index = np.argmax(predictions)
    return emotion_labels[emotion_index]


=======
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image

model = tf.keras.models.load_model("./Model/FER_DATA.keras")

emotion_labels = ['Angry', 'Happy', 'Sad',  'Neutral']

def predict_emotion(image_path: str) -> str:
    img = Image.open(image_path).convert('L').resize((48, 48))
    img_array = np.array(img) / 255.0
    img_array = img_array.reshape(1, 48, 48, 1)

    predictions = model.predict(img_array)
    emotion_index = np.argmax(predictions)
    return emotion_labels[emotion_index]


>>>>>>> db2d7506b05bc40d8aca21622d9cb938ce61cd04
