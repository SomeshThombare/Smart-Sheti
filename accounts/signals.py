from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser, FarmerProfile, AdminProfile


@receiver(post_save, sender=CustomUser)
def ensure_related_profile_exists(sender, instance, created, **kwargs):
    """
    Ensure the correct related profile exists for each user.

    - Farmer user  -> FarmerProfile
    - Admin user   -> AdminProfile

    Safe for both create and update operations.
    get_or_create() avoids duplicate profile creation.
    """

    if instance.role == CustomUser.RoleChoices.FARMER:
        FarmerProfile.objects.get_or_create(
            user=instance,
            defaults={
                "gender": FarmerProfile.GenderChoices.MALE,
                "village": "Default Village",
                "taluka": "Default Taluka",
                "district": "Default District",
                "state": "Maharashtra",
                "pincode": "400001",
                "full_address": "Default Address",
            }
        )

    elif instance.role == CustomUser.RoleChoices.ADMIN:
        AdminProfile.objects.get_or_create(
            user=instance,
            defaults={
                "admin_secret_code": "shubham@1592",
            }
        )