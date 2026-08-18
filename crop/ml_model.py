import os

import joblib
import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ML_DIR = os.path.join(BASE_DIR, "ml")
MODEL_PATH = os.path.join(ML_DIR, "crop_model.pkl")
ACCURACY_PATH = os.path.join(ML_DIR, "accuracy.txt")


FEATURE_COLUMNS = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]


_model = None


def load_model():
    global _model

    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "Model not found. Run: python crop/train_model.py"
        )

    _model = joblib.load(MODEL_PATH)

    return _model


def validate_input(
    nitrogen,
    phosphorus,
    potassium,
    temperature,
    humidity,
    ph,
    rainfall,
):
    values = {
        "Nitrogen": nitrogen,
        "Phosphorus": phosphorus,
        "Potassium": potassium,
        "Temperature": temperature,
        "Humidity": humidity,
        "pH": ph,
        "Rainfall": rainfall,
    }

    for field_name, value in values.items():
        if value in [None, ""]:
            raise ValueError(f"{field_name} value is required.")

        try:
            values[field_name] = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} must be a valid number.")

    if values["Nitrogen"] < 0:
        raise ValueError("Nitrogen cannot be negative.")

    if values["Phosphorus"] < 0:
        raise ValueError("Phosphorus cannot be negative.")

    if values["Potassium"] < 0:
        raise ValueError("Potassium cannot be negative.")

    if values["Temperature"] < -50 or values["Temperature"] > 100:
        raise ValueError("Temperature must be between -50 and 100.")

    if values["Humidity"] < 0 or values["Humidity"] > 100:
        raise ValueError("Humidity must be between 0 and 100.")

    if values["pH"] < 0 or values["pH"] > 14:
        raise ValueError("pH must be between 0 and 14.")

    if values["Rainfall"] < 0:
        raise ValueError("Rainfall cannot be negative.")

    return values


def predict_crop(
    nitrogen,
    phosphorus,
    potassium,
    temperature,
    humidity,
    ph,
    rainfall,
):
    model = load_model()

    values = validate_input(
        nitrogen=nitrogen,
        phosphorus=phosphorus,
        potassium=potassium,
        temperature=temperature,
        humidity=humidity,
        ph=ph,
        rainfall=rainfall,
    )

    input_data = pd.DataFrame(
        [[
            values["Nitrogen"],
            values["Phosphorus"],
            values["Potassium"],
            values["Temperature"],
            values["Humidity"],
            values["pH"],
            values["Rainfall"],
        ]],
        columns=FEATURE_COLUMNS,
    )

    prediction = model.predict(input_data)

    return str(prediction[0]).title()


def predict_crop_with_probability(
    nitrogen,
    phosphorus,
    potassium,
    temperature,
    humidity,
    ph,
    rainfall,
):
    model = load_model()

    values = validate_input(
        nitrogen=nitrogen,
        phosphorus=phosphorus,
        potassium=potassium,
        temperature=temperature,
        humidity=humidity,
        ph=ph,
        rainfall=rainfall,
    )

    input_data = pd.DataFrame(
        [[
            values["Nitrogen"],
            values["Phosphorus"],
            values["Potassium"],
            values["Temperature"],
            values["Humidity"],
            values["pH"],
            values["Rainfall"],
        ]],
        columns=FEATURE_COLUMNS,
    )

    prediction = model.predict(input_data)[0]

    probability = None

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(input_data)[0]
        probability = round(max(probabilities) * 100, 2)

    return {
        "predicted_crop": str(prediction).title(),
        "confidence": probability,
    }


def get_model_accuracy():
    if os.path.exists(ACCURACY_PATH):
        with open(ACCURACY_PATH, "r", encoding="utf-8") as file:
            accuracy = file.read().strip()

        if accuracy:
            return accuracy

    return "Not available"