import logging
from typing import Optional

from .chatbot import DEFAULT_SYSTEM_PROMPT, get_ai_response

logger = logging.getLogger("chatbot")


class ChatbotService:
    """
    Smart Sheti Chatbot Service.

    Purpose:
    - Keep service layer clean.
    - Avoid duplicate OpenRouter API code.
    - Use chatbot.py for actual AI response generation.
    """

    @staticmethod
    def get_response(
        user_message: Optional[str],
        system_prompt: Optional[str] = None,
    ) -> str:
        try:
            return get_ai_response(
                user_message=user_message,
                system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
            )

        except Exception as exc:
            logger.exception("ChatbotService response generation failed.")
            return f"⚠️ {str(exc)}"

    @staticmethod
    def get_admin_response(user_message: Optional[str]) -> str:
        admin_prompt = f"""
{DEFAULT_SYSTEM_PROMPT}

ADMIN MODE:
You are Smart Sheti Admin AI Assistant.

Admin rules:
- Help admin understand dashboard reports, farmer records, crop reports, fertilizer reports, disease reports, image reports and PDF reports.
- Help admin manage crops, fertilizers, schemes, equipment rental, marketplace, complaints and reports.
- If admin asks crop disease information, always follow full disease format.
- Never give only disease names.
- Always include Disease Name, Scientific Name, Severity, Symptoms, Cause, Control/Management, Recommended Treatment, Prevention and Safety Precautions.
- Disease category accuracy is mandatory.
- Give professional, clear and structured answers.
""".strip()

        return ChatbotService.get_response(
            user_message=user_message,
            system_prompt=admin_prompt,
        )

    @staticmethod
    def get_farmer_response(user_message: Optional[str]) -> str:
        farmer_prompt = f"""
{DEFAULT_SYSTEM_PROMPT}

FARMER MODE:
You are Smart Sheti Farmer/User AI Assistant.

Farmer rules:
- Give simple, practical and step-by-step farming help.
- Help with crop disease, pest control, fertilizer, soil, irrigation, weather advice and government schemes.
- If farmer asks crop disease information, always follow full disease format.
- Never give only disease names.
- Always include Disease Name, Scientific Name, Severity, Symptoms, Cause, Control/Management, Recommended Treatment, Prevention and Safety Precautions.
- If user asks in Marathi, reply fully in Marathi.
- Avoid long technical answers unless farmer asks.
""".strip()

        return ChatbotService.get_response(
            user_message=user_message,
            system_prompt=farmer_prompt,
        )