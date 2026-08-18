# accounts/backends.py

from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import CustomUser


class UsernameEmailMobileBackend(ModelBackend):
    """
    Custom authentication backend.

    Allows login using:
    - username
    - email
    - mobile_number
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Django may pass username using USERNAME_FIELD
        if username is None:
            username = kwargs.get("username")

        # Required fields check
        if not username or not password:
            return None

        try:
            user = CustomUser.objects.get(
                Q(username__iexact=username)
                | Q(email__iexact=username)
                | Q(mobile_number=username)
            )

        except CustomUser.DoesNotExist:
            return None

        except CustomUser.MultipleObjectsReturned:
            return None

        # Password and active user check
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None