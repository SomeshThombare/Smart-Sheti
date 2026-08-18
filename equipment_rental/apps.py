from django.apps import AppConfig


class EquipmentRentalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "equipment_rental"

    def ready(self):
        import equipment_rental.signals