import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Equipment, EquipmentBooking


logger = logging.getLogger(__name__)


@receiver(pre_save, sender=EquipmentBooking)
def cache_old_booking_values(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_equipment_id = None
        return

    try:
        old_booking = EquipmentBooking.objects.only(
            "equipment_id",
        ).get(pk=instance.pk)

        instance._old_equipment_id = old_booking.equipment_id

    except EquipmentBooking.DoesNotExist:
        instance._old_equipment_id = None


@receiver(post_save, sender=EquipmentBooking)
def update_equipment_status_after_booking_save(sender, instance, created, **kwargs):
    try:
        update_equipment_status(instance.equipment)

        old_equipment_id = getattr(instance, "_old_equipment_id", None)

        if old_equipment_id and old_equipment_id != instance.equipment_id:
            old_equipment = Equipment.objects.filter(pk=old_equipment_id).first()

            if old_equipment:
                update_equipment_status(old_equipment)

    except Exception:
        logger.exception("Error updating equipment status after booking save.")


@receiver(post_delete, sender=EquipmentBooking)
def update_equipment_status_after_booking_delete(sender, instance, **kwargs):
    try:
        if instance.equipment_id:
            update_equipment_status(instance.equipment)

    except Exception:
        logger.exception("Error updating equipment status after booking delete.")


def update_equipment_status(equipment):
    if not equipment:
        return

    today = timezone.localdate()

    active_booking_exists = EquipmentBooking.objects.filter(
        equipment=equipment,
        booking_status__in=[
            EquipmentBooking.BookingStatusChoices.PENDING,
            EquipmentBooking.BookingStatusChoices.CONFIRMED,
        ],
        booking_end_date__gte=today,
    ).exists()

    new_status = (
        Equipment.EquipmentStatusChoices.RENTED
        if active_booking_exists
        else Equipment.EquipmentStatusChoices.AVAILABLE
    )

    if equipment.equipment_status != new_status:
        equipment.equipment_status = new_status
        equipment.save(update_fields=[
            "equipment_status",
            "updated_at",
        ])