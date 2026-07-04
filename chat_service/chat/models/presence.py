"""
Presence model.

Stores the last-known online status and last_seen timestamp for users
who have connected to the chat service.

Design decisions:
  - user_id is the primary key (one record per user, no UUID PK needed).
  - online / last_seen are stored in BOTH PostgreSQL (Presence model) AND Redis.
  - Redis is the source of truth for real-time presence (TTL-based).
  - PostgreSQL is used for:
      a) Persistent "last seen" timestamp displayed in the conversation list.
      b) Fallback when Redis is unavailable.
  - The model is write-heavy but read from Redis, so the DB record is updated
    on disconnect and on the first online event (not every heartbeat).
"""
from django.db import models
from django.utils import timezone


class Presence(models.Model):
    """Persistent record of a user's online status and last seen time."""

    # UUID string — cross-service reference to auth_service user
    # Used as the PK so there is exactly one Presence row per user.
    user_id = models.UUIDField(primary_key=True, db_index=True)

    online = models.BooleanField(default=False, db_index=True)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = "chat"
        db_table = "chat_presence"

    def __str__(self) -> str:
        status = "online" if self.online else "offline"
        return f"Presence({self.user_id}) {status} last_seen={self.last_seen}"

    @classmethod
    def upsert(cls, user_id: str, online: bool) -> "Presence":
        """Create or update the presence record for a user."""
        obj, _ = cls.objects.update_or_create(
            user_id=user_id,
            defaults={"online": online, "last_seen": timezone.now()},
        )
        return obj
