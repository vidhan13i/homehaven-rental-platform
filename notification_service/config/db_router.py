"""
Database router for notification_service.
Routes all notification app models to notification_db.
All other models (admin, auth, sessions) remain on default postgres DB.
"""


class NotificationRouter:
    APP_LABEL = "notification"
    DB_ALIAS = "notification"

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.APP_LABEL:
            return self.DB_ALIAS
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.APP_LABEL:
            return self.DB_ALIAS
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label == self.APP_LABEL
            or obj2._meta.app_label == self.APP_LABEL
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.APP_LABEL:
            return db == self.DB_ALIAS
        return db == "default"
