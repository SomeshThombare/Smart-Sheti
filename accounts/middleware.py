import time

from django.conf import settings
from django.contrib.auth import logout
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import translation


class UserLanguageMiddleware:
    """
    Custom middleware to set application language.

    Priority:
    1. Logged-in user's language_preference from database
    2. Session stored language
    3. Default language from settings
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_languages = {
            code for code, _name in getattr(settings, "LANGUAGES", [])
        }
        self.default_language = getattr(settings, "LANGUAGE_CODE", "en")
        self.language_cookie_name = getattr(
            settings,
            "LANGUAGE_COOKIE_NAME",
            "django_language"
        )

    def __call__(self, request):
        language = None

        user = getattr(request, "user", None)

        # 1. logged-in user preference
        if user and getattr(user, "is_authenticated", False):
            user_language = getattr(user, "language_preference", None)
            if user_language and user_language in self.allowed_languages:
                language = user_language

        # 2. session language
        if not language and hasattr(request, "session"):
            session_language = request.session.get(self.language_cookie_name)
            if session_language and session_language in self.allowed_languages:
                language = session_language

        # 3. default language
        if not language or language not in self.allowed_languages:
            language = self.default_language

        translation.activate(language)
        request.LANGUAGE_CODE = language

        if hasattr(request, "session"):
            request.session[self.language_cookie_name] = language

        response = self.get_response(request)
        response["Content-Language"] = language

        # optional: set language cookie also
        response.set_cookie(
            self.language_cookie_name,
            language,
            max_age=60 * 60 * 24 * 365,  # 1 year
            httponly=False,
            samesite="Lax",
        )

        return response


class AutoLogoutMiddleware:
    """
    Auto logout user after inactivity.
    Works only for web/session login.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = getattr(settings, "AUTO_LOGOUT_DELAY", 1800)

        default_exempt_paths = {
            "/accounts/login/",
            "/accounts/logout/",
            "/admin/login/",
            "/admin/logout/",
        }

        configured_exempt_paths = set(
            getattr(settings, "AUTO_LOGOUT_EXEMPT_PATHS", [])
        )

        self.exempt_paths = default_exempt_paths.union(configured_exempt_paths)

        self.exempt_prefixes = (
            "/static/",
            "/media/",
            "/admin/jsi18n/",
            "/accounts/api/login/",
            "/accounts/api/send-otp/",
            "/accounts/api/verify-otp/",
        )

    def __call__(self, request):
        user = getattr(request, "user", None)

        if not user or not getattr(user, "is_authenticated", False):
            return self.get_response(request)

        current_path = request.path

        # skip exempt exact paths
        if current_path in self.exempt_paths:
            return self.get_response(request)

        # skip exempt prefixes
        if current_path.startswith(self.exempt_prefixes):
            return self.get_response(request)

        # only session-based requests should be auto-logged-out
        if not hasattr(request, "session"):
            return self.get_response(request)

        current_time = int(time.time())
        last_activity_time = request.session.get("last_activity_time")

        if last_activity_time is not None:
            elapsed_time = current_time - int(last_activity_time)

            if elapsed_time > self.timeout:
                logout(request)

                # if API request, return JSON instead of redirect
                if current_path.startswith("/accounts/api/"):
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Session expired due to inactivity. Please login again."
                        },
                        status=401
                    )

                return redirect(getattr(settings, "LOGIN_URL", "/accounts/login/"))

        request.session["last_activity_time"] = current_time

        response = self.get_response(request)
        return response