import os

services = [
    "auth_service",
    "profile_service",
    "listings_service",
    "building_service",
    "application_service",
    "reviews_service",
    "notification_service"
]

pytest_ini_content = """[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = --nomigrations --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
"""

for service in services:
    ini_path = os.path.join(service, "pytest.ini")
    with open(ini_path, "w") as f:
        f.write(pytest_ini_content)
    
    # Also create a tests folder inside the main app if it exists
    app_map = {
        "auth_service": "authentication",
        "profile_service": "profiles_app",
        "listings_service": "listings",
        "building_service": "building",
        "application_service": "application",
        "reviews_service": "reviews",
        "notification_service": "notification"
    }
    
    app_name = app_map[service]
    test_dir = os.path.join(service, app_name, "tests")
    os.makedirs(test_dir, exist_ok=True)
    init_file = os.path.join(test_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write("")

print("Pytest configs and test directories created.")
