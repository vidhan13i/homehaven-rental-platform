class ProfilesRouter:
    """
    Routes all DB operations for the 'profiles_app' app
    to the dedicated 'profiles_app' database.
    """

    route_app_labels = {"profiles_app"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "profiles_app"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "profiles_app"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels
            and obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == "profiles_app"
        return None
