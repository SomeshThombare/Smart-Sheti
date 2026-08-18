import os
import pandas as pd
import numpy as np
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from django.conf import settings


FERTILIZER_INFO = {
    "Urea": {
        "description": "Most common nitrogen fertilizer (46% N). Fast-acting and water-soluble.",
        "amount": "80-120 kg/ha",
        "how_to_use": "Broadcast or side dressing; incorporate into soil to prevent volatilization.",
        "timing": "Split into 2-3 doses: basal + top dressing at tillering/growth stages.",
        "tips": "Avoid surface application without irrigation. Mix well into moist soil.",
    },
    "DAP": {
        "description": "Di-Ammonium Phosphate (18% N, 46% P₂O₅). Best basal phosphatic fertilizer.",
        "amount": "50-80 kg/ha",
        "how_to_use": "Broadcast and incorporate at sowing/planting as basal dose.",
        "timing": "At sowing time — place near seed zone (2-3 cm below seed).",
        "tips": "Do not mix with Urea directly. Ideal for phosphorus-deficient soils.",
    },
    "MOP": {
        "description": "Muriate of Potash (60% K₂O). Primary source of potassium.",
        "amount": "40-70 kg/ha",
        "how_to_use": "Broadcast and mix into soil before planting or at growth stages.",
        "timing": "Basal or split with first irrigation. Avoid pre-harvest application.",
        "tips": "Improves fruit quality, drought tolerance, and disease resistance.",
    },
    "SSP": {
        "description": "Single Super Phosphate (16% P₂O₅, 11% S, 21% Ca). Supplies both P and S.",
        "amount": "100-150 kg/ha",
        "how_to_use": "Basal application; broadcast and incorporate before sowing.",
        "timing": "At sowing/planting as a basal dose.",
        "tips": "Good for sulphur-deficient soils. Economical phosphorus source.",
    },
    "19:19:19 NPK": {
        "description": "Balanced NPK fertilizer with equal N, P, K (19% each). Fully water-soluble.",
        "amount": "3-5 g/litre for foliar; 50-80 kg/ha soil application.",
        "how_to_use": "Foliar spray or fertigation through drip/sprinkler irrigation.",
        "timing": "During active growth phases and critical nutrient demand periods.",
        "tips": "Ideal for fertigation. Avoid foliar spray during intense heat or rain.",
    },
    "20:20:20 NPK": {
        "description": "Equal ratio water-soluble NPK. Used for foliar feeding and drip fertigation.",
        "amount": "3-5 g/litre foliar; 40-60 kg/ha soil.",
        "how_to_use": "Foliar spray or through fertigation system.",
        "timing": "During active growth and at flowering stage.",
        "tips": "Fully water-soluble, no residue. Ideal for precision fertigation.",
    },
    "10:26:26 NPK": {
        "description": "Low N, high P & K NPK complex. Good for root development and grain filling.",
        "amount": "50-100 kg/ha",
        "how_to_use": "Basal or split application in soil.",
        "timing": "At sowing as basal or early growth stage top-dressing.",
        "tips": "Suitable for crops needing strong root system and better fruiting.",
    },
    "13:32:26 NPK": {
        "description": "Complex NPK with higher P content. Promotes early root and shoot development.",
        "amount": "50-80 kg/ha",
        "how_to_use": "Basal application incorporated at sowing.",
        "timing": "At sowing time as a basal dose.",
        "tips": "Good for phosphorus-demanding crops at establishment stage.",
    },
    "12:32:16 NPK": {
        "description": "NPK complex with high phosphorus. Boosts flowering and fruit set.",
        "amount": "50-80 kg/ha",
        "how_to_use": "Soil incorporation or fertigation.",
        "timing": "Pre-sowing basal or at transplanting stage.",
        "tips": "Enhances root proliferation and early establishment.",
    },
    "Ammonium Sulphate": {
        "description": "Contains 21% N and 24% S. Suitable for alkaline soils.",
        "amount": "100-150 kg/ha",
        "how_to_use": "Broadcast and incorporate, or side-dress.",
        "timing": "Basal or top dressing at vegetative stages.",
        "tips": "Acidifies soil slightly — good for alkaline/calcareous soils.",
    },
    "Ferrous Sulphate": {
        "description": "Iron sulphate (20% Fe). Corrects iron-deficiency chlorosis.",
        "amount": "25-50 kg/ha soil; 0.5% foliar spray.",
        "how_to_use": "Soil application or foliar spray on chlorotic plants.",
        "timing": "When yellowing of young leaves appears.",
        "tips": "Foliar spray gives faster results.",
    },
    "White Potash": {
        "description": "Potassium Sulphate (50% K₂O). Chloride-free potassium source.",
        "amount": "50-75 kg/ha",
        "how_to_use": "Soil application or fertigation.",
        "timing": "Basal or split application before and during fruiting.",
        "tips": "Preferred for chloride-sensitive crops.",
    },
}

DEFAULT_INFO = {
    "description": "Balanced crop nutrition fertilizer.",
    "amount": "60-100 kg/ha",
    "how_to_use": "Broadcast or fertigation as recommended.",
    "timing": "Basal or split application.",
    "tips": "Consult local agriculture officer for precise dose.",
}


class FertilizerMLModel:
    MODEL_CACHE_PATH = None

    def __init__(self):
        self.clf = None
        self.le_crop = LabelEncoder()
        self.le_soil = LabelEncoder()
        self.le_fert = LabelEncoder()
        self._trained = False
        self._dataset_path = None
        self._df = None
        self._init_paths()

    def _init_paths(self):
        self._dataset_path = os.path.join(
            settings.BASE_DIR,
            "ai_engine",
            "data",
            "Crop and fertilizer dataset.csv"
        )
        FertilizerMLModel.MODEL_CACHE_PATH = os.path.join(
            settings.BASE_DIR,
            "ai_engine",
            "data",
            "fertilizer_model_cache.pkl"
        )

    def _clean_dataset(self, df):
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]

        required_columns = [
            "Crop", "Soil_color", "Nitrogen", "Phosphorus",
            "Potassium", "pH", "Rainfall", "Temperature", "Fertilizer"
        ]

        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Dataset missing required columns: {', '.join(missing)}")

        if "Link" not in df.columns:
            df["Link"] = "#"

        df["Crop"] = df["Crop"].astype(str).str.strip().str.title()
        df["Soil_color"] = df["Soil_color"].astype(str).str.strip().str.title()
        df["Fertilizer"] = df["Fertilizer"].astype(str).str.strip()
        df["Link"] = df["Link"].fillna("#").astype(str).str.strip()

        numeric_columns = ["Nitrogen", "Phosphorus", "Potassium", "pH", "Rainfall", "Temperature"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=required_columns).copy()

        if df.empty:
            raise ValueError("Dataset has no valid rows after cleaning.")

        return df

    def _build_feature_frame(self, crop_enc, soil_enc, n, p, k, ph, rainfall, temperature):
        return pd.DataFrame(
            [[crop_enc, soil_enc, n, p, k, ph, rainfall, temperature]],
            columns=[
                "Crop_enc", "Soil_enc", "Nitrogen", "Phosphorus",
                "Potassium", "pH", "Rainfall", "Temperature"
            ]
        )

    def _load_and_train(self):
        if not os.path.exists(self._dataset_path):
            raise FileNotFoundError(f"Dataset not found: {self._dataset_path}")

        df = pd.read_csv(self._dataset_path)
        df = self._clean_dataset(df)
        self._df = df

        df["Crop_enc"] = self.le_crop.fit_transform(df["Crop"])
        df["Soil_enc"] = self.le_soil.fit_transform(df["Soil_color"])
        df["Fert_enc"] = self.le_fert.fit_transform(df["Fertilizer"])

        X = df[
            ["Crop_enc", "Soil_enc", "Nitrogen", "Phosphorus",
             "Potassium", "pH", "Rainfall", "Temperature"]
        ]
        y = df["Fert_enc"]

        self.clf = RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
        self.clf.fit(X, y)
        self._trained = True

        try:
            joblib.dump(
                {
                    "clf": self.clf,
                    "le_crop": self.le_crop,
                    "le_soil": self.le_soil,
                    "le_fert": self.le_fert,
                    "df": self._df,
                },
                self.MODEL_CACHE_PATH
            )
        except Exception:
            pass

    def _load_from_cache(self):
        try:
            if self.MODEL_CACHE_PATH and os.path.exists(self.MODEL_CACHE_PATH):
                data = joblib.load(self.MODEL_CACHE_PATH)
                self.clf = data["clf"]
                self.le_crop = data["le_crop"]
                self.le_soil = data["le_soil"]
                self.le_fert = data["le_fert"]
                self._df = data["df"]

                if self.clf is None or self._df is None:
                    return False

                self._trained = True
                return True
        except Exception:
            return False
        return False

    def _ensure_trained(self):
        if not self._trained:
            if not self._load_from_cache():
                self._load_and_train()

    def predict(self, input_data):
        try:
            self._ensure_trained()

            crop = str(input_data.get("Crop", "")).strip().title()
            soil = str(input_data.get("Soil_color", "")).strip().title()
            n = float(input_data.get("Nitrogen", 0))
            p = float(input_data.get("Phosphorus", 0))
            k = float(input_data.get("Potassium", 0))
            ph = float(input_data.get("pH", 7.0))
            rainfall = float(input_data.get("Rainfall", 1000))
            temperature = float(input_data.get("Temperature", 25))

            if not crop:
                return {"status": "error", "message": "Crop is required."}
            if not soil:
                return {"status": "error", "message": "Soil color is required."}

            if crop not in self.le_crop.classes_:
                return {"status": "error", "message": f"Crop '{crop}' not in training data."}
            if soil not in self.le_soil.classes_:
                return {"status": "error", "message": f"Soil color '{soil}' not in training data."}

            crop_enc = self.le_crop.transform([crop])[0]
            soil_enc = self.le_soil.transform([soil])[0]

            X_input = self._build_feature_frame(
                crop_enc, soil_enc, n, p, k, ph, rainfall, temperature
            )

            proba = self.clf.predict_proba(X_input)[0]
            top3_idx = np.argsort(proba)[::-1][:3]

            link_map = (
                self._df[["Fertilizer", "Link"]]
                .drop_duplicates()
                .set_index("Fertilizer")["Link"]
                .to_dict()
            ) if self._df is not None else {}

            total = n + p + k
            npk_ratio = {
                "N": round((n / total) * 100, 1) if total else 0,
                "P": round((p / total) * 100, 1) if total else 0,
                "K": round((k / total) * 100, 1) if total else 0,
            }

            recommendations = []
            for idx in top3_idx:
                fert_name = self.le_fert.inverse_transform([idx])[0]
                confidence = round(float(proba[idx]) * 100, 1)
                info = FERTILIZER_INFO.get(fert_name, DEFAULT_INFO)

                recommendations.append({
                    "fertilizer_name": fert_name,
                    "confidence": confidence,
                    "description": info["description"],
                    "amount": info["amount"],
                    "how_to_use": info["how_to_use"],
                    "timing": info["timing"],
                    "tips": info["tips"],
                    "link": link_map.get(fert_name, "#"),
                })

            if not recommendations:
                return {"status": "error", "message": "No fertilizer recommendation generated."}

            top1 = recommendations[0]

            return {
                "status": "success",
                "fertilizer_name": top1["fertilizer_name"],
                "quantity": top1["amount"],
                "recommendations": recommendations,
                "npk_ratio": npk_ratio,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }