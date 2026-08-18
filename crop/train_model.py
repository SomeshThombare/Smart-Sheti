import os
import json

import joblib
import kagglehub
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ML_DIR = os.path.join(BASE_DIR, "ml")
MODEL_PATH = os.path.join(ML_DIR, "crop_model.pkl")
ACCURACY_PATH = os.path.join(ML_DIR, "accuracy.txt")
REPORT_PATH = os.path.join(ML_DIR, "classification_report.json")


FEATURE_COLUMNS = [
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
]

TARGET_COLUMN = "label"


def get_csv_file(dataset_path):
    for file_name in os.listdir(dataset_path):
        if file_name.endswith(".csv"):
            return os.path.join(dataset_path, file_name)

    raise FileNotFoundError("CSV file not found in downloaded dataset.")


def train_model():
    os.makedirs(ML_DIR, exist_ok=True)

    print("Downloading dataset...")

    dataset_path = kagglehub.dataset_download(
        "madhuraatmarambhagat/crop-recommendation-dataset"
    )

    csv_path = get_csv_file(dataset_path)

    print("Reading dataset...")

    df = pd.read_csv(csv_path)

    required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df = df.dropna()

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
    )

    print("Training model...")

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    accuracy_percent = round(accuracy * 100, 2)

    report = classification_report(
        y_test,
        y_pred,
        output_dict=True,
        zero_division=0,
    )

    joblib.dump(model, MODEL_PATH)

    with open(ACCURACY_PATH, "w", encoding="utf-8") as file:
        file.write(str(accuracy_percent))

    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(f"Model Accuracy: {accuracy_percent}%")
    print(f"Model Saved: {MODEL_PATH}")
    print(f"Accuracy Saved: {ACCURACY_PATH}")
    print(f"Classification Report Saved: {REPORT_PATH}")

    return model, accuracy_percent


if __name__ == "__main__":
    train_model()