import logging
import random
import re
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from .models import OTPVerification

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 10
OTP_RESEND_SECONDS = 30


# =========================================================
# Normalize Helpers
# =========================================================

def normalize_username(username: str) -> str:
    if not username:
        return ""

    username = str(username).strip().lower()
    username = re.sub(r"\s+", "", username)

    return username


def normalize_email(email: str) -> str:
    if not email:
        return ""

    return str(email).strip().lower()


def normalize_mobile_number(mobile_number: str) -> str:
    if not mobile_number:
        return ""

    mobile_number = str(mobile_number).strip()
    mobile_number = mobile_number.replace(" ", "").replace("-", "")

    if mobile_number.startswith("+91"):
        mobile_number = mobile_number[3:]
    elif mobile_number.startswith("91") and len(mobile_number) == 12:
        mobile_number = mobile_number[2:]

    return mobile_number


# =========================================================
# OTP Helpers
# =========================================================

def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def mask_email(email: str) -> str:
    if not email:
        return "No Email"

    email = str(email).strip().lower()

    if "@" not in email:
        return email

    name, domain = email.split("@", 1)

    if len(name) <= 2:
        return f"{name[0]}***@{domain}"

    return f"{name[:2]}***@{domain}"


def mask_mobile_number(mobile_number: str) -> str:
    if not mobile_number:
        return "No Mobile"

    mobile_number = str(mobile_number)

    if len(mobile_number) >= 10:
        return mobile_number[:3] + "*****" + mobile_number[-2:]

    return "**********"


def to_e164_indian_number(mobile_number: str) -> str:
    mobile_number = normalize_mobile_number(mobile_number)
    return f"+91{mobile_number}"


# =========================================================
# Send Email OTP
# =========================================================

def send_email_otp(email: str, otp: str) -> dict:
    try:
        subject = "Smart Sheti Email OTP"
        message = (
            f"Dear User,\n\n"
            f"Your Smart Sheti email OTP is: {otp}\n"
            f"This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.\n\n"
            f"Please do not share this OTP with anyone.\n\n"
            f"Regards,\n"
            f"Smart Sheti Team"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        logger.info("Email OTP sent successfully to %s", mask_email(email))

        return {
            "success": True,
            "message": "Email OTP sent successfully.",
        }

    except Exception:
        logger.exception("Email OTP sending failed for %s", mask_email(email))

        return {
            "success": False,
            "message": "Failed to send email OTP.",
        }


# =========================================================
# Send Mobile OTP
# =========================================================

def send_mobile_otp(mobile_number: str, otp: str) -> dict:
    sms_number = to_e164_indian_number(mobile_number)

    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
    )

    message_body = (
        f"Smart Sheti OTP: {otp}. "
        f"Do not share this code with anyone. "
        f"Valid for {OTP_EXPIRY_MINUTES} minutes."
    )

    try:
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=sms_number,
        )

        logger.info(
            "SMS sent successfully to %s | SID=%s",
            mask_mobile_number(sms_number),
            message.sid,
        )

        return {
            "success": True,
            "sid": message.sid,
            "message": "Mobile OTP sent successfully.",
        }

    except TwilioRestException as e:
        logger.exception(
            "Twilio SMS failed for %s",
            mask_mobile_number(sms_number),
        )

        error_message = str(e)

        if "21608" in error_message or "unverified" in error_message.lower():
            return {
                "success": False,
                "message": (
                    "This mobile number is not verified in your Twilio trial account. "
                    "Please verify the number in Twilio Console or upgrade your Twilio account."
                ),
            }

        return {
            "success": False,
            "message": "SMS sending failed.",
        }

    except Exception:
        logger.exception(
            "Unexpected SMS error for %s",
            mask_mobile_number(sms_number),
        )

        return {
            "success": False,
            "message": "Unexpected SMS sending error.",
        }


# =========================================================
# Detect OTP Send Type
# =========================================================

def detect_send_to(email=None, mobile_number=None, send_to="auto") -> str:
    email = normalize_email(email)
    mobile_number = normalize_mobile_number(mobile_number)

    send_to = str(send_to or "auto").strip().lower()

    if send_to not in ["auto", "both", "email", "sms"]:
        raise ValueError("Invalid send_to value. Use auto, both, email, or sms.")

    if send_to == "auto":
        if email and mobile_number:
            return "both"

        if email:
            return "email"

        if mobile_number:
            return "sms"

        raise ValueError("Email or mobile number is required for OTP.")

    if send_to == "both" and (not email or not mobile_number):
        raise ValueError("Email and mobile number are required for both OTP.")

    if send_to == "email" and not email:
        raise ValueError("Email is required for email OTP.")

    if send_to == "sms" and not mobile_number:
        raise ValueError("Mobile number is required for SMS OTP.")

    return send_to


# =========================================================
# Create OTP Record
# =========================================================

def create_otp_record(
    email=None,
    mobile_number=None,
    send_to="auto",
    purpose="general",
) -> dict:
    """
    send_to:
    - auto  = detects automatically
    - both  = email OTP + mobile OTP
    - email = only email OTP
    - sms   = only mobile OTP
    """

    email = normalize_email(email)
    mobile_number = normalize_mobile_number(mobile_number)
    purpose = str(purpose or "general").strip().lower()

    send_to = detect_send_to(
        email=email,
        mobile_number=mobile_number,
        send_to=send_to,
    )

    filter_data = {
        "purpose": purpose,
    }

    if send_to == "email":
        filter_data["email"] = email

    elif send_to == "sms":
        filter_data["mobile_number"] = mobile_number

    else:
        filter_data["email"] = email
        filter_data["mobile_number"] = mobile_number

    existing_otp = OTPVerification.objects.filter(
        **filter_data
    ).order_by("-created_at").first()

    if existing_otp:
        time_difference = timezone.now() - existing_otp.created_at

        if time_difference < timedelta(seconds=OTP_RESEND_SECONDS):
            wait_seconds = OTP_RESEND_SECONDS - int(
                time_difference.total_seconds()
            )

            return {
                "success": False,
                "send_to": send_to,
                "purpose": purpose,
                "email_result": {
                    "success": False,
                    "message": f"Please wait {wait_seconds} seconds before requesting OTP again.",
                },
                "sms_result": {
                    "success": False,
                    "message": f"Please wait {wait_seconds} seconds before requesting OTP again.",
                },
            }

    email_otp = generate_otp() if send_to in ["both", "email"] else None
    mobile_otp = generate_otp() if send_to in ["both", "sms"] else None
    expiry_time = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    OTPVerification.objects.filter(**filter_data).delete()

    otp_record = OTPVerification.objects.create(
        email=email if send_to in ["both", "email"] else None,
        mobile_number=mobile_number if send_to in ["both", "sms"] else None,
        email_otp=email_otp,
        mobile_otp=mobile_otp,
        purpose=purpose,
        is_email_verified=False,
        is_mobile_verified=False,
        is_verified=False,
        expires_at=expiry_time,
    )

    email_result = {
        "success": True,
        "message": "Email OTP not required.",
    }

    sms_result = {
        "success": True,
        "message": "Mobile OTP not required.",
    }

    if send_to in ["both", "email"]:
        email_result = send_email_otp(email, email_otp)

    if send_to in ["both", "sms"]:
        sms_result = send_mobile_otp(mobile_number, mobile_otp)

    logger.info(
        "OTP created for email=%s mobile=%s purpose=%s send_to=%s",
        mask_email(email),
        mask_mobile_number(mobile_number),
        purpose,
        send_to,
    )

    return {
        "success": email_result.get("success", False)
        and sms_result.get("success", False),
        "otp_id": otp_record.id,
        "send_to": send_to,
        "purpose": purpose,
        "email_result": email_result,
        "sms_result": sms_result,
    }


# =========================================================
# Verify OTP
# =========================================================

def verify_otp(
    email=None,
    mobile_number=None,
    email_otp=None,
    mobile_otp=None,
    send_to="auto",
    purpose="general",
):
    email = normalize_email(email)
    mobile_number = normalize_mobile_number(mobile_number)
    email_otp = str(email_otp).strip() if email_otp else ""
    mobile_otp = str(mobile_otp).strip() if mobile_otp else ""
    purpose = str(purpose or "general").strip().lower()

    try:
        send_to = detect_send_to(
            email=email,
            mobile_number=mobile_number,
            send_to=send_to,
        )
    except ValueError as exc:
        return False, str(exc)

    filter_data = {
        "purpose": purpose,
    }

    if send_to == "email":
        filter_data["email"] = email

    elif send_to == "sms":
        filter_data["mobile_number"] = mobile_number

    else:
        filter_data["email"] = email
        filter_data["mobile_number"] = mobile_number

    try:
        otp_record = OTPVerification.objects.filter(
            **filter_data
        ).latest("created_at")

    except OTPVerification.DoesNotExist:
        return False, "OTP record not found. Please request OTP again."

    if timezone.now() > otp_record.expires_at:
        return False, "OTP has expired. Please request a new OTP."

    if send_to == "email":
        if otp_record.is_email_verified:
            return True, "Email OTP already verified."

        if otp_record.email_otp != email_otp:
            return False, "Invalid email OTP."

        otp_record.is_email_verified = True
        otp_record.is_verified = True

        otp_record.save(
            update_fields=[
                "is_email_verified",
                "is_verified",
            ]
        )

        return True, "Email OTP verified successfully."

    if send_to == "sms":
        if otp_record.is_mobile_verified:
            return True, "Mobile OTP already verified."

        if otp_record.mobile_otp != mobile_otp:
            return False, "Invalid mobile OTP."

        otp_record.is_mobile_verified = True
        otp_record.is_verified = True

        otp_record.save(
            update_fields=[
                "is_mobile_verified",
                "is_verified",
            ]
        )

        return True, "Mobile OTP verified successfully."

    if otp_record.is_email_verified and otp_record.is_mobile_verified:
        return True, "Email OTP and mobile OTP already verified."

    if otp_record.email_otp != email_otp:
        return False, "Invalid email OTP."

    if otp_record.mobile_otp != mobile_otp:
        return False, "Invalid mobile OTP."

    otp_record.is_email_verified = True
    otp_record.is_mobile_verified = True
    otp_record.is_verified = True

    otp_record.save(
        update_fields=[
            "is_email_verified",
            "is_mobile_verified",
            "is_verified",
        ]
    )

    logger.info(
        "OTP verified successfully for email=%s mobile=%s purpose=%s send_to=%s",
        mask_email(email),
        mask_mobile_number(mobile_number),
        purpose,
        send_to,
    )

    return True, "OTP verified successfully."


# =========================================================
# Check OTP Verified
# =========================================================

def is_otp_verified(
    email=None,
    mobile_number=None,
    send_to="auto",
    purpose="general",
) -> bool:
    email = normalize_email(email)
    mobile_number = normalize_mobile_number(mobile_number)
    purpose = str(purpose or "general").strip().lower()

    try:
        send_to = detect_send_to(
            email=email,
            mobile_number=mobile_number,
            send_to=send_to,
        )
    except ValueError:
        return False

    filter_data = {
        "purpose": purpose,
    }

    if send_to == "email":
        filter_data["email"] = email
        filter_data["is_email_verified"] = True

    elif send_to == "sms":
        filter_data["mobile_number"] = mobile_number
        filter_data["is_mobile_verified"] = True

    else:
        filter_data["email"] = email
        filter_data["mobile_number"] = mobile_number
        filter_data["is_email_verified"] = True
        filter_data["is_mobile_verified"] = True

    return OTPVerification.objects.filter(**filter_data).exists()