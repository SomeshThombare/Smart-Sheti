import os
import json
import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
from django.conf import settings


MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "disease_detection",
    "crop_disease_model.keras"
)

CLASS_NAMES_PATH = os.path.join(
    settings.BASE_DIR,
    "disease_detection",
    "class_names.json"
)

model = None
class_names_cache = None


TREATMENT_ENGLISH = {
    "Corn__Common_Rust": "For common rust, spray a propiconazole or mancozeb-based fungicide. Remove heavily infected leaves and avoid overhead irrigation.",
    "Corn__Gray_Leaf_Spot": "For gray leaf spot, spray mancozeb or another recommended fungicide. Maintain proper plant spacing and remove crop residue.",
    "Corn__Healthy": "The corn crop is healthy. Continue regular monitoring and maintain balanced irrigation and fertilizer.",
    "Corn__Northern_Leaf_Blight": "For northern leaf blight, spray a suitable fungicide such as mancozeb or propiconazole. Remove infected plant debris.",

    "Potato__Early_Blight": "For early blight, spray mancozeb or chlorothalonil. Remove infected leaves and avoid water stress.",
    "Potato__Late_Blight": "For late blight, spray metalaxyl + mancozeb. Avoid excess moisture and improve field drainage.",
    "Potato__Healthy": "The potato crop is healthy. Continue regular monitoring and avoid excess watering.",

    "Rice__Brown_Spot": "For brown spot, spray a suitable fungicide and apply balanced fertilizer, especially potassium and nitrogen as required.",
    "Rice__Healthy": "The rice crop is healthy. Continue regular monitoring and maintain proper water management.",
    "Rice__Leaf_Blast": "For leaf blast, spray a tricyclazole-based fungicide. Avoid excess nitrogen fertilizer.",
    "Rice__Neck_Blast": "For neck blast, spray recommended fungicide after consulting an agriculture expert. Avoid dense planting.",

    "Sugarcane_Bacterial Blight": "Remove infected leaves and avoid waterlogging. Use disease-free planting material.",
    "Sugarcane_Healthy": "The sugarcane crop is healthy. Continue regular monitoring and maintain proper field sanitation.",
    "Sugarcane_Red Rot": "Remove and destroy infected sugarcane plants. Use disease-free seed cane and avoid ratooning infected fields.",

    "Wheat__Brown_Rust": "For brown rust, spray a propiconazole-based fungicide. Monitor the field regularly during humid weather.",
    "Wheat__Healthy": "The wheat crop is healthy. Continue regular monitoring.",
    "Wheat__Yellow_Rust": "For yellow rust, spray a suitable fungicide such as propiconazole or tebuconazole after expert advice.",
}


CROP_DISPLAY_NAMES = {
    "Corn": "Corn",
    "Potato": "Potato",
    "Rice": "Rice",
    "Sugarcane": "Sugarcane",
    "Wheat": "Wheat",
}


DISEASE_DISPLAY_NAMES = {
    "Corn__Common_Rust": "Corn - Common Rust",
    "Corn__Gray_Leaf_Spot": "Corn - Gray Leaf Spot",
    "Corn__Healthy": "Corn - Healthy",
    "Corn__Northern_Leaf_Blight": "Corn - Northern Leaf Blight",

    "Potato__Early_Blight": "Potato - Early Blight",
    "Potato__Late_Blight": "Potato - Late Blight",
    "Potato__Healthy": "Potato - Healthy",

    "Rice__Brown_Spot": "Rice - Brown Spot",
    "Rice__Healthy": "Rice - Healthy",
    "Rice__Leaf_Blast": "Rice - Leaf Blast",
    "Rice__Neck_Blast": "Rice - Neck Blast",

    "Sugarcane_Bacterial Blight": "Sugarcane - Bacterial Blight",
    "Sugarcane_Healthy": "Sugarcane - Healthy",
    "Sugarcane_Red Rot": "Sugarcane - Red Rot",

    "Wheat__Brown_Rust": "Wheat - Brown Rust",
    "Wheat__Healthy": "Wheat - Healthy",
    "Wheat__Yellow_Rust": "Wheat - Yellow Rust",
}


def normalize_class_name(class_name):
    return str(class_name).strip()


def load_class_names():
    global class_names_cache

    if class_names_cache is not None:
        return class_names_cache

    if not os.path.exists(CLASS_NAMES_PATH):
        raise FileNotFoundError(
            "class_names.json not found. Please run train_model.py first."
        )

    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as f:
        class_names_cache = json.load(f)

    if not isinstance(class_names_cache, list) or len(class_names_cache) == 0:
        raise ValueError("class_names.json must contain a non-empty list.")

    return class_names_cache


def get_model():
    global model

    if model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                "crop_disease_model.keras not found. Please train model first."
            )

        model = tf.keras.models.load_model(MODEL_PATH)

    return model


def clean_name(class_name):
    class_name = normalize_class_name(class_name)

    return (
        class_name
        .replace("___", " - ")
        .replace("__", " - ")
        .replace("_", " ")
    )


def get_crop_name(class_name):
    class_name = normalize_class_name(class_name)

    if "___" in class_name:
        crop_key = class_name.split("___")[0]

    elif "__" in class_name:
        crop_key = class_name.split("__")[0]

    elif "_" in class_name:
        crop_key = class_name.split("_")[0]

    else:
        crop_key = class_name.split()[0]

    crop_key = crop_key.replace("_", " ").strip()

    return CROP_DISPLAY_NAMES.get(crop_key, crop_key)


def get_disease_display_name(class_name):
    class_name = normalize_class_name(class_name)
    return DISEASE_DISPLAY_NAMES.get(class_name, clean_name(class_name))


def preprocess_image(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        image = image.resize((224, 224))

        image_array = np.array(image).astype("float32")

        # Do NOT divide by 255 here if EfficientNet preprocess_input
        # is already included inside your trained model.
        image_array = np.expand_dims(image_array, axis=0)

        return image_array

    except FileNotFoundError:
        raise FileNotFoundError("Uploaded image file was not found.")

    except UnidentifiedImageError:
        raise ValueError("Invalid image file. Please upload a valid JPG, JPEG, or PNG image.")

    except Exception as e:
        raise ValueError(f"Image preprocessing failed: {str(e)}")


def get_suggestion(class_name, confidence):
    class_name_lower = class_name.lower()

    if "healthy" in class_name_lower:
        return "The crop appears healthy. Continue regular monitoring, proper irrigation, and balanced fertilizer use."

    if confidence < 50:
        return (
            "The prediction confidence is very low. Please upload a clear close-up leaf image "
            "with good lighting and consult an agriculture expert."
        )

    if confidence < 70:
        return (
            "The result has low confidence. Please upload another clear leaf image from a different angle "
            "or consult an agriculture expert."
        )

    return (
        "If the disease is severe or spreading quickly, consult a nearby agriculture officer "
        "or agriculture expert before applying chemicals."
    )


def predict_disease(image_path):
    loaded_model = get_model()
    class_names = load_class_names()

    img_array = preprocess_image(image_path)

    predictions = loaded_model.predict(img_array, verbose=0)

    if predictions is None or len(predictions) == 0:
        raise ValueError("Model did not return any prediction.")

    predicted_index = int(np.argmax(predictions[0]))

    if predicted_index >= len(class_names):
        raise ValueError(
            "Prediction index is out of range. Please check model and class_names.json."
        )

    confidence = float(predictions[0][predicted_index] * 100)

    class_name = normalize_class_name(class_names[predicted_index])

    crop_name = get_crop_name(class_name)
    disease_name = get_disease_display_name(class_name)

    treatment = TREATMENT_ENGLISH.get(
        class_name,
        "Please consult a nearby agriculture expert for proper treatment."
    )

    suggestion = get_suggestion(class_name, confidence)

    confidence = round(confidence, 2)

    print("Prediction:", class_name, "Confidence:", confidence)

    return {
        "success": True,

        "crop_name": crop_name,
        "disease_name": disease_name,
        "confidence": confidence,

        "treatment": treatment,
        "suggestion": suggestion,

        # Old frontend compatibility keys
        "treatment_marathi": treatment,
        "suggestion_marathi": suggestion,

        # Extra useful keys
        "class_name": class_name,
        "predicted_index": predicted_index,
    }