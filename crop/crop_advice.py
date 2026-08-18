def _to_float(value, field_name):
    if value in [None, ""]:
        raise ValueError(f"{field_name} value is required.")

    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")


def get_crop_advice(
    nitrogen,
    phosphorus,
    potassium,
    temperature,
    humidity,
    ph,
    rainfall,
):
    nitrogen = _to_float(nitrogen, "Nitrogen")
    phosphorus = _to_float(phosphorus, "Phosphorus")
    potassium = _to_float(potassium, "Potassium")
    temperature = _to_float(temperature, "Temperature")
    humidity = _to_float(humidity, "Humidity")
    ph = _to_float(ph, "pH")
    rainfall = _to_float(rainfall, "Rainfall")

    if nitrogen < 0:
        raise ValueError("Nitrogen cannot be negative.")

    if phosphorus < 0:
        raise ValueError("Phosphorus cannot be negative.")

    if potassium < 0:
        raise ValueError("Potassium cannot be negative.")

    if temperature < -50 or temperature > 100:
        raise ValueError("Temperature must be between -50 and 100.")

    if humidity < 0 or humidity > 100:
        raise ValueError("Humidity must be between 0 and 100.")

    if ph < 0 or ph > 14:
        raise ValueError("pH must be between 0 and 14.")

    if rainfall < 0:
        raise ValueError("Rainfall cannot be negative.")

    advice = {}

    if nitrogen < 40:
        advice["nitrogen_status"] = "Low Nitrogen"
        advice["nitrogen_advice"] = "Apply nitrogen-rich fertilizer like Urea or Compost."
    elif nitrogen <= 90:
        advice["nitrogen_status"] = "Medium Nitrogen"
        advice["nitrogen_advice"] = "Nitrogen level is suitable for most crops."
    else:
        advice["nitrogen_status"] = "High Nitrogen"
        advice["nitrogen_advice"] = "Avoid excessive nitrogen fertilizer usage."

    if phosphorus < 30:
        advice["phosphorus_status"] = "Low Phosphorus"
        advice["phosphorus_advice"] = "Use phosphorus-rich fertilizers like DAP or Bone Meal."
    elif phosphorus <= 70:
        advice["phosphorus_status"] = "Medium Phosphorus"
        advice["phosphorus_advice"] = "Phosphorus level is balanced."
    else:
        advice["phosphorus_status"] = "High Phosphorus"
        advice["phosphorus_advice"] = "Reduce phosphorus fertilizer application."

    if potassium < 30:
        advice["potassium_status"] = "Low Potassium"
        advice["potassium_advice"] = "Apply Potash fertilizer to improve crop growth."
    elif potassium <= 80:
        advice["potassium_status"] = "Medium Potassium"
        advice["potassium_advice"] = "Potassium level is suitable."
    else:
        advice["potassium_status"] = "High Potassium"
        advice["potassium_advice"] = "Avoid excess potassium fertilizer usage."

    if ph < 6:
        advice["ph_status"] = "Acidic Soil"
        advice["ph_advice"] = "Add lime to reduce soil acidity."
    elif ph <= 7.5:
        advice["ph_status"] = "Neutral Soil"
        advice["ph_advice"] = "Soil pH is ideal for most crops."
    else:
        advice["ph_status"] = "Alkaline Soil"
        advice["ph_advice"] = "Use gypsum or organic matter to improve soil condition."

    if rainfall < 60:
        advice["rainfall_status"] = "Low Rainfall"
        advice["rainfall_advice"] = "Irrigation is recommended."
    elif rainfall <= 150:
        advice["rainfall_status"] = "Medium Rainfall"
        advice["rainfall_advice"] = "Rainfall level is suitable for farming."
    else:
        advice["rainfall_status"] = "High Rainfall"
        advice["rainfall_advice"] = "Ensure proper drainage to avoid waterlogging."

    if temperature < 20:
        advice["temperature_status"] = "Low Temperature"
        advice["temperature_advice"] = "Cold weather crops are more suitable."
    elif temperature <= 35:
        advice["temperature_status"] = "Suitable Temperature"
        advice["temperature_advice"] = "Temperature is ideal for crop growth."
    else:
        advice["temperature_status"] = "High Temperature"
        advice["temperature_advice"] = "Provide sufficient irrigation and shade if possible."

    if humidity < 40:
        advice["humidity_status"] = "Low Humidity"
        advice["humidity_advice"] = "Increase irrigation frequency if required."
    elif humidity <= 80:
        advice["humidity_status"] = "Medium Humidity"
        advice["humidity_advice"] = "Humidity level is suitable."
    else:
        advice["humidity_status"] = "High Humidity"
        advice["humidity_advice"] = "Monitor crops for fungal diseases."

    if (
        40 <= nitrogen <= 90
        and 30 <= phosphorus <= 70
        and 30 <= potassium <= 80
        and 6 <= ph <= 7.5
        and 20 <= temperature <= 35
        and 40 <= humidity <= 80
        and 60 <= rainfall <= 150
    ):
        advice["overall_condition"] = "Good Condition"
        advice["overall_advice"] = "All major crop conditions are suitable."
    else:
        advice["overall_condition"] = "Needs Improvement"
        advice["overall_advice"] = "Some soil or weather values need improvement."

    return advice