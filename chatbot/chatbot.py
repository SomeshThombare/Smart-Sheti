import base64
import logging
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


DEFAULT_SYSTEM_PROMPT = """
You are Smart Sheti — an expert AI Agriculture Assistant for Indian Farmers.

Your goal:
Provide accurate, practical, farmer-friendly and actionable agricultural guidance.

LANGUAGE RULES:
- If the user writes in Marathi, always reply fully in Marathi.
- Disease names may remain in English, but explanations must be in Marathi.
- If the user writes in English, reply in English.
- Use simple farmer-friendly language.
- Avoid unnecessary technical jargon.

AGRICULTURE RULES:
- Focus on Indian farming conditions.
- Give practical crop, soil, fertilizer, irrigation, pest and disease advice.
- Prioritize crop health, yield improvement and farmer safety.

CROP DISEASE RULES:
- Never provide only disease names.
- Never provide one-line disease descriptions.
- For every crop disease, always include:
  1. Disease Name
  2. Scientific Name / Pathogen if known
  3. Severity Level: Low / Medium / High
  4. Symptoms
  5. Cause
  6. Control / Management
  7. Recommended Spray / Treatment
  8. Prevention Tips
  9. Safety Precautions

IF USER ASKS ALL DISEASES OF ANY CROP:
- Include 8 to 12 important/common diseases if available.
- Keep each disease complete but concise.
- Do not end the response incomplete.
- Classify diseases into:
  1. Fungal Diseases
  2. Bacterial Diseases
  3. Viral Diseases
  4. Nematode Diseases
  5. Nutrient Deficiency / Physiological Problems

CATEGORY ACCURACY RULES:
- Fungal diseases must contain only fungal diseases.
- Bacterial diseases must contain only bacterial diseases.
- Viral diseases must contain only viral diseases.
- Nematode diseases must contain only nematode problems.
- Nutrient / physiological section must contain only nutrient or physiological problems.
- Do not mix virus diseases inside bacterial diseases.
- Do not mix nutrient deficiencies inside fungal/bacterial/viral diseases.

For tomato disease list, include important diseases such as:
- Early Blight
- Late Blight
- Septoria Leaf Spot
- Powdery Mildew
- Fusarium Wilt
- Verticillium Wilt
- Leaf Mold
- Bacterial Wilt
- Bacterial Spot
- Tomato Mosaic Virus
- Tomato Yellow Leaf Curl Virus
- Tomato Spotted Wilt Virus
- Root Knot Nematode
- Blossom End Rot

For each disease provide:
- Disease Name
- Scientific Name / Pathogen if known
- Severity
- Symptoms
- Cause
- Control / Management
- Recommended Spray / Treatment
- Prevention Tips
- Safety Precautions

SPRAY / TREATMENT RULES:
- Mention active ingredient where possible.
- Mention approximate commonly used dosage only when known.
- Always say: Follow product label instructions.
- Never recommend overdose.
- Mention safety: wear gloves, mask, avoid spraying in strong wind, avoid spraying in hot afternoon.

IMAGE ANALYSIS RULES:
When image is uploaded:
1. Identify crop if possible.
2. Identify disease, pest, nutrient deficiency, weed or physical damage.
3. Provide confidence level: High / Medium / Low.
4. Give observed symptoms.
5. Give possible cause.
6. Give treatment.
7. Give prevention.
8. If image is unclear, say image quality is insufficient and ask for close-up photo.

PEST MANAGEMENT RULES:
For pest questions always provide:
- Pest Name
- Symptoms
- Damage caused
- Control measures
- Recommended pesticide if applicable
- Safety precautions

FERTILIZER RULES:
For fertilizer questions mention:
- Fertilizer name
- Approximate dosage if commonly known
- Application timing
- Precautions

GOVERNMENT SCHEME RULES:
For scheme questions provide:
- Scheme name
- Eligibility
- Benefits
- Required documents
- Application process

SAFETY RULES:
- Do not suggest unsafe chemical usage.
- Do not guarantee diagnosis from unclear images.
- Always advise reading product label before pesticide/fungicide use.
- For severe crop loss, suggest contacting local Krishi Seva Kendra or agriculture officer.

OUTPUT RULES:
- Use headings.
- Use bullet points.
- Keep response structured.
- Keep advice practical and farmer-friendly.
- For disease-related questions, complete format is mandatory.
- For long disease lists, be complete but concise.
""".strip()


def _safe_strip(value: Any) -> str:
    return str(value or "").strip()


def _build_headers() -> Dict[str, str]:
    api_key = _safe_strip(getattr(settings, "OPENROUTER_API_KEY", ""))

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing. Please add it in .env file.")

    if api_key.startswith("os.getenv"):
        raise RuntimeError(
            "OPENROUTER_API_KEY value is wrong. "
            "In .env file use only: OPENROUTER_API_KEY=sk-or-v1-your_key"
        )

    if not api_key.startswith("sk-or-v1-"):
        raise RuntimeError(
            "OPENROUTER_API_KEY format is invalid. It should start with sk-or-v1-"
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    http_referer = _safe_strip(
        getattr(settings, "OPENROUTER_HTTP_REFERER", "http://127.0.0.1:8000")
    )
    x_title = _safe_strip(
        getattr(settings, "OPENROUTER_X_TITLE", "Smart Sheti")
    )

    if http_referer and not http_referer.startswith("os.getenv"):
        headers["HTTP-Referer"] = http_referer

    if x_title and not x_title.startswith("os.getenv"):
        headers["X-Title"] = x_title

    return headers


def _to_data_url(file_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _normalize_prompt_text(user_message: Optional[str], fallback: str) -> str:
    text = _safe_strip(user_message)
    return text if text else fallback


def _build_user_content(
    user_message: Optional[str] = None,
    image_data: Optional[bytes] = None,
    image_mime: Optional[str] = None,
    pdf_data: Optional[bytes] = None,
) -> List[Dict[str, Any]]:
    content: List[Dict[str, Any]] = []

    if image_data:
        prompt_text = _normalize_prompt_text(
            user_message,
            (
                "Analyze this farm crop image. Identify crop, visible disease/pest/nutrient issue, "
                "confidence level, symptoms, cause, treatment, spray suggestion, prevention and safety precautions."
            ),
        )

        content.append({"type": "text", "text": prompt_text})
        content.append({
            "type": "image_url",
            "image_url": {
                "url": _to_data_url(image_data, image_mime or "image/jpeg")
            },
        })
        return content

    if pdf_data:
        prompt_text = _normalize_prompt_text(
            user_message,
            "Analyze this PDF and summarize it in simple farmer-friendly language.",
        )

        content.append({"type": "text", "text": prompt_text})
        content.append({
            "type": "file",
            "file": {
                "filename": "uploaded_document.pdf",
                "file_data": _to_data_url(pdf_data, "application/pdf"),
            },
        })
        return content

    content.append({
        "type": "text",
        "text": _normalize_prompt_text(user_message, "Hello"),
    })

    return content


def _choose_model(
    image_data: Optional[bytes] = None,
    pdf_data: Optional[bytes] = None,
) -> str:
    if image_data or pdf_data:
        model = _safe_strip(
            getattr(settings, "OPENROUTER_VISION_MODEL", "openai/gpt-4o")
        )
    else:
        model = _safe_strip(
            getattr(settings, "OPENROUTER_MODEL", "openai/gpt-4o-mini")
        )

    if not model or model.startswith("os.getenv"):
        return "openai/gpt-4o-mini"

    return model


def _choose_max_tokens(
    image_data: Optional[bytes] = None,
    pdf_data: Optional[bytes] = None,
) -> int:
    if image_data:
        return 2500

    if pdf_data:
        return 4000

    return 5000


def _extract_text_from_response_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: List[str] = []

        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = _safe_strip(item.get("text"))
                if text:
                    parts.append(text)

        return "\n".join(parts).strip()

    return ""


def _parse_openrouter_error(response: requests.Response) -> str:
    status_code = response.status_code
    error_text = response.text or ""

    try:
        error_json = response.json()
        error_message = (
            error_json.get("error", {}).get("message")
            or error_json.get("message")
            or error_text
        )
    except Exception:
        error_message = error_text

    if status_code == 401:
        return (
            "OpenRouter authentication failed. "
            "API key invalid, deleted, expired, or copied incorrectly. "
            f"Details: {error_message}"
        )

    if status_code == 402:
        return "OpenRouter credits are insufficient. Please add credits or reduce token usage."

    if status_code == 404:
        return "OpenRouter model not found or this model does not support this input type."

    if status_code == 408:
        return "OpenRouter request timeout. Please try again."

    if status_code == 429:
        return "OpenRouter rate limit reached. Please try again after some time."

    if status_code >= 500:
        return "OpenRouter server error. Please try again after some time."

    return f"OpenRouter API returned {status_code}: {error_message}"


def get_ai_response(
    user_message: Optional[str] = None,
    image_data: Optional[bytes] = None,
    image_mime: Optional[str] = None,
    pdf_data: Optional[bytes] = None,
    system_prompt: Optional[str] = None,
) -> str:
    final_system_prompt = _safe_strip(system_prompt) or DEFAULT_SYSTEM_PROMPT
    model_name = _choose_model(image_data=image_data, pdf_data=pdf_data)
    max_tokens = _choose_max_tokens(image_data=image_data, pdf_data=pdf_data)

    messages = [
        {
            "role": "system",
            "content": final_system_prompt,
        },
        {
            "role": "user",
            "content": _build_user_content(
                user_message=user_message,
                image_data=image_data,
                image_mime=image_mime,
                pdf_data=pdf_data,
            ),
        },
    ]

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.30,
        "max_tokens": max_tokens,
    }

    logger.info(
        "OpenRouter request started | model=%s | has_image=%s | has_pdf=%s | max_tokens=%s",
        model_name,
        bool(image_data),
        bool(pdf_data),
        max_tokens,
    )

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=_build_headers(),
            json=payload,
            timeout=90,
        )

        if response.status_code != 200:
            logger.error(
                "OpenRouter API error [%s]: %s",
                response.status_code,
                response.text,
            )
            raise RuntimeError(_parse_openrouter_error(response))

        data = response.json()
        choices = data.get("choices", [])

        if not choices:
            logger.error("OpenRouter response missing choices: %s", data)
            raise RuntimeError("No response choices returned from OpenRouter.")

        message = choices[0].get("message", {})
        content = message.get("content", "")
        final_text = _extract_text_from_response_content(content)

        if not final_text:
            logger.warning("OpenRouter returned empty content: %s", data)
            return "Sorry, I could not generate a response."

        logger.info("OpenRouter request completed successfully.")
        return final_text

    except requests.exceptions.Timeout as exc:
        logger.exception("OpenRouter request timeout")
        raise RuntimeError("Request timed out while contacting OpenRouter.") from exc

    except requests.exceptions.RequestException as exc:
        logger.exception("OpenRouter network request exception")
        raise RuntimeError(f"Network request failed: {str(exc)}") from exc

    except Exception:
        logger.exception("OpenRouter unexpected error")
        raise