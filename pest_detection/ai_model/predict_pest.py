# pest_detection/ai_model/predict_pest.py

import os
import json
import logging

import numpy as np
import tensorflow as tf

from PIL import Image, UnidentifiedImageError
from django.conf import settings


logger = logging.getLogger(__name__)

BASE_DIR = settings.BASE_DIR

MODEL_PATH = os.path.join(
    BASE_DIR,
    "pest_detection",
    "ai_model",
    "models",
    "pest_model.keras"
)

CLASS_NAMES_PATH = os.path.join(
    BASE_DIR,
    "pest_detection",
    "ai_model",
    "models",
    "pest_class_names.json"
)

IMG_SIZE = 224
CONFIDENCE_THRESHOLD = 60.0

model = None
class_names = None


def load_model_once():
    global model, class_names

    if model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

        model = tf.keras.models.load_model(MODEL_PATH)

    if class_names is None:
        if not os.path.exists(CLASS_NAMES_PATH):
            raise FileNotFoundError(f"Class names file not found: {CLASS_NAMES_PATH}")

        with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as file:
            class_names = json.load(file)

        if not isinstance(class_names, list):
            raise ValueError("pest_class_names.json must contain a list.")

        if len(class_names) == 0:
            raise ValueError("pest_class_names.json is empty.")

    return model, class_names


def get_severity(confidence):
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0

    if confidence >= 90:
        return "HIGH"

    if confidence >= 70:
        return "MEDIUM"

    if confidence >= 60:
        return "LOW"

    return "UNCLEAR"


def get_treatment_priority(confidence):
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0

    if confidence >= 90:
        return "Immediate Action Required"

    if confidence >= 70:
        return "Treat Within 3 Days"

    if confidence >= 60:
        return "Monitor Closely"

    return "Upload Clear Image Again"


def build_response(
    status_value,
    pest_name,
    confidence=0,
    message="",
    class_name="",
    predicted_index=None,
    top_predictions=None,
    success=False,
):
    try:
        confidence = round(float(confidence), 2)
    except (TypeError, ValueError):
        confidence = 0

    try:
        predicted_index = int(predicted_index)
    except (TypeError, ValueError):
        predicted_index = None

    severity = get_severity(confidence)
    treatment_priority = get_treatment_priority(confidence)

    return {
        "success": success,
        "status": status_value,
        "pest_name": pest_name,
        "confidence": confidence,
        "class_name": class_name or pest_name,
        "predicted_index": predicted_index,
        "message": message,
        "top_predictions": top_predictions or [],
        "severity": severity,
        "treatment_priority": treatment_priority,
    }


def validate_image_path(image_path):
    if not image_path:
        return build_response(
            status_value="error",
            pest_name="Error",
            confidence=0,
            message="Image path is empty.",
            class_name="Error",
            predicted_index=None,
            top_predictions=[],
            success=False,
        )

    if not os.path.exists(image_path):
        return build_response(
            status_value="error",
            pest_name="Error",
            confidence=0,
            message="Image file not found.",
            class_name="Error",
            predicted_index=None,
            top_predictions=[],
            success=False,
        )

    return None


def load_and_prepare_image(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
    except UnidentifiedImageError:
        return None, build_response(
            status_value="error",
            pest_name="Error",
            confidence=0,
            message="Invalid image file. Please upload JPG, PNG, JPEG or WEBP image.",
            class_name="Error",
            predicted_index=None,
            top_predictions=[],
            success=False,
        )

    if image.width < 100 or image.height < 100:
        return None, build_response(
            status_value="low_confidence",
            pest_name="Unknown / Image Too Small",
            confidence=0,
            message="Image size खूप small आहे. Clear insect close-up image upload करा.",
            class_name="Unknown / Image Too Small",
            predicted_index=None,
            top_predictions=[],
            success=False,
        )

    image = image.resize((IMG_SIZE, IMG_SIZE))

    image_array = np.array(image).astype("float32")
    image_array = np.expand_dims(image_array, axis=0)

    image_array = tf.keras.applications.efficientnet.preprocess_input(image_array)

    return image_array, None


def normalize_predictions(predictions):
    predictions = np.array(predictions)

    if predictions.ndim == 2:
        predictions = predictions[0]

    if predictions.ndim != 1:
        raise ValueError("Invalid model prediction output shape.")

    return predictions


def get_top_predictions(predictions, loaded_class_names, top_k=5):
    top_k = min(top_k, len(predictions))
    top_indices = predictions.argsort()[-top_k:][::-1]

    top_predictions = []

    for idx in top_indices:
        idx = int(idx)

        class_name = loaded_class_names[idx]
        pest_name = class_name.replace("_", " ").title()
        confidence = round(float(predictions[idx]) * 100, 2)

        top_predictions.append({
            "pest_name": pest_name,
            "class_name": class_name,
            "predicted_index": idx,
            "confidence": confidence,
            "severity": get_severity(confidence),
            "treatment_priority": get_treatment_priority(confidence),
        })

    return top_indices, top_predictions


def predict_pest(image_path):
    try:
        loaded_model, loaded_class_names = load_model_once()

        path_error = validate_image_path(image_path)
        if path_error:
            return path_error

        image_array, image_error = load_and_prepare_image(image_path)
        if image_error:
            return image_error

        predictions = loaded_model.predict(image_array, verbose=0)
        predictions = normalize_predictions(predictions)

        if len(predictions) != len(loaded_class_names):
            return build_response(
                status_value="error",
                pest_name="Error",
                confidence=0,
                message=(
                    f"Model output classes ({len(predictions)}) and "
                    f"class names ({len(loaded_class_names)}) mismatch."
                ),
                class_name="Error",
                predicted_index=None,
                top_predictions=[],
                success=False,
            )

        top_indices, top_predictions = get_top_predictions(
            predictions=predictions,
            loaded_class_names=loaded_class_names,
            top_k=5,
        )

        best_index = int(top_indices[0])
        class_name = loaded_class_names[best_index]
        pest_name = class_name.replace("_", " ").title()
        confidence = round(float(predictions[best_index]) * 100, 2)

        if confidence < CONFIDENCE_THRESHOLD:
            return build_response(
                status_value="low_confidence",
                pest_name="Unknown / Pest Not Clear",
                confidence=confidence,
                message="Image मध्ये pest clear दिसत नाही. कृपया clear insect close-up image upload करा.",
                class_name=class_name,
                predicted_index=best_index,
                top_predictions=top_predictions,
                success=False,
            )

        return build_response(
            status_value="success",
            pest_name=pest_name,
            confidence=confidence,
            message="Pest detected successfully.",
            class_name=class_name,
            predicted_index=best_index,
            top_predictions=top_predictions,
            success=True,
        )

    except Exception as e:
        logger.exception("Pest prediction error")

        return build_response(
            status_value="error",
            pest_name="Error",
            confidence=0,
            message=str(e),
            class_name="Error",
            predicted_index=None,
            top_predictions=[],
            success=False,
        )