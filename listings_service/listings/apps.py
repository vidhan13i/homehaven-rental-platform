from django.apps import AppConfig

class ListingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'listings'  # ✅ Fixed: was 'listings-service' (dashes break Python imports)