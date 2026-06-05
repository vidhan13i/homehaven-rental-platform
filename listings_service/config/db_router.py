class ListingsRouter:
    """
    Routes all database reads/writes for the 'listings' app
    to the dedicated 'listings' database.

    Concept → DB Router: Django lets you define multiple databases
    and a router that decides which database each model uses.
    """
    route_app_labels = {"listings"}  # ✅ Fixed: was "listings-service"

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "listings"        # ✅ Fixed: was "listings-service"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "listings"        # ✅ Fixed: was "listings-service"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels and
            obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == "listings"  # ✅ Fixed: was "listings-service"
        return None