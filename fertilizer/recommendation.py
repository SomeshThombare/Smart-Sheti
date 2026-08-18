from ai_engine.ml_model import FertilizerMLModel


class FertilizerRecommendation:
    def __init__(self, crop_type, soil_data):
        self.crop_type = str(crop_type).strip().title() if crop_type else ""
        self.soil_data = soil_data if isinstance(soil_data, dict) else {}
        self.ml_model = FertilizerMLModel()

    def _to_float(self, value, default=0.0):
        try:
            if value in [None, ""]:
                return float(default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _get_soil_color(self):
        return str(
            self.soil_data.get("soil_color")
            or self.soil_data.get("Soil_color")
            or ""
        ).strip().title()

    def get_input_payload(self):
        return {
            "Crop": self.crop_type,
            "Soil_color": self._get_soil_color(),
            "Nitrogen": self._to_float(self.soil_data.get("N", 0)),
            "Phosphorus": self._to_float(self.soil_data.get("P", 0)),
            "Potassium": self._to_float(self.soil_data.get("K", 0)),
            "pH": self._to_float(self.soil_data.get("pH", 6.5)),
            "Rainfall": self._to_float(self.soil_data.get("rainfall", 1000)),
            "Temperature": self._to_float(self.soil_data.get("temperature", 25)),
        }

    def validate_payload(self, payload):
        errors = {}

        if not payload["Crop"]:
            errors["Crop"] = "Crop is required."

        if not payload["Soil_color"]:
            errors["Soil_color"] = "Soil color is required."

        if payload["Nitrogen"] < 0:
            errors["Nitrogen"] = "Nitrogen cannot be negative."

        if payload["Phosphorus"] < 0:
            errors["Phosphorus"] = "Phosphorus cannot be negative."

        if payload["Potassium"] < 0:
            errors["Potassium"] = "Potassium cannot be negative."

        if payload["pH"] < 0 or payload["pH"] > 14:
            errors["pH"] = "pH must be between 0 and 14."

        if payload["Rainfall"] < 0:
            errors["Rainfall"] = "Rainfall cannot be negative."

        if payload["Temperature"] < -50 or payload["Temperature"] > 100:
            errors["Temperature"] = "Temperature must be between -50 and 100."

        return errors

    def get_recommendation_result(self):
        try:
            payload = self.get_input_payload()
            errors = self.validate_payload(payload)

            if errors:
                return {
                    "status": "error",
                    "message": "Invalid fertilizer input data.",
                    "errors": errors,
                    "input": payload,
                }

            result = self.ml_model.predict(payload)

            if not isinstance(result, dict):
                return {
                    "status": "error",
                    "message": "Invalid ML model response format.",
                    "errors": {
                        "result": "ML model must return dictionary response."
                    },
                    "input": payload,
                }

            return result

        except Exception as e:
            return {
                "status": "error",
                "message": "Error while generating fertilizer recommendation.",
                "errors": {
                    "detail": str(e)
                },
                "input": self.get_input_payload(),
            }