"""
Database router for chat_service.

Routes all models from the 'chat' app to the dedicated 'chat' database (chat_db).
All other models (admin, auth, contenttypes, sessions) use the 'default' database.

Mirrors the exact same pattern as:
  - listings_service/config/db_router.py  (ListingsRouter)
  - profile_service/config/db_router.py   (ProfilesRouter)
  - auth_service/config/db_router.py      (AuthRouter)
"""


class ChatRouter:
    """Routes all 'chat' app models to the 'chat' database (chat_db)."""

    route_app_labels = {"chat"}

    def db_for_read(self, model, **hints) -> str | None:
        if model._meta.app_label in self.route_app_labels:
            return "chat"
        return None

    def db_for_write(self, model, **hints) -> str | None:
        if model._meta.app_label in self.route_app_labels:
            return "chat"
        return None

    def allow_relation(self, obj1, obj2, **hints) -> bool | None:
        if (
            obj1._meta.app_label in self.route_app_labels
            and obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(
        self, db: str, app_label: str, model_name: str = None, **hints
    ) -> bool | None:
        if app_label in self.route_app_labels:
            return db == "chat"
        return None
