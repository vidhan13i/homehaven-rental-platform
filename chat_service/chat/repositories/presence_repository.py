"""
Presence Repository.

Manages the dual-storage presence system:
  - Redis: real-time source of truth (TTL-based, expires if no heartbeat)
  - PostgreSQL: persistent last_seen record (survives Redis flush)

Redis key format:
  presence:{user_id}
  Type: Hash
  Fields: {online: "1"/"0", last_seen: ISO datetime string}
  TTL: CHAT_PRESENCE_TTL_SECONDS (default 35s)

A user is considered online if the Redis key exists AND online == "1".
When the TTL expires (no heartbeat for 35s), the user is automatically offline.
"""

import logging
from typing import Optional

import redis
from django.conf import settings
from django.utils import timezone

from chat.models import Presence

logger = logging.getLogger("chat.repositories.presence")

_redis_client: Optional[redis.Redis] = None
PRESENCE_KEY_PREFIX = "presence"


def _get_redis() -> redis.Redis:
    """Singleton Redis client for presence operations."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _redis_client


class PresenceRepository:
    """Data access layer for user presence (Redis + PostgreSQL)."""

    @staticmethod
    def _redis_key(user_id: str) -> str:
        return f"{PRESENCE_KEY_PREFIX}:{user_id}"

    @staticmethod
    def set_online(user_id: str) -> None:
        """
        Mark a user as online.
        Updates Redis (real-time) and PostgreSQL (persistent).
        """
        key = PresenceRepository._redis_key(user_id)
        now_iso = timezone.now().isoformat()
        ttl = settings.CHAT_PRESENCE_TTL_SECONDS

        try:
            r = _get_redis()
            pipe = r.pipeline()
            pipe.hset(key, mapping={"online": "1", "last_seen": now_iso})
            pipe.expire(key, ttl)
            pipe.execute()
        except redis.RedisError as exc:
            logger.error("Redis error in set_online for %s: %s", user_id, str(exc))

        # Update persistent record (fire-and-forget is acceptable here)
        try:
            Presence.upsert(user_id=user_id, online=True)
        except Exception as exc:
            logger.error("DB error in set_online for %s: %s", user_id, str(exc))

    @staticmethod
    def set_offline(user_id: str) -> None:
        """
        Mark a user as offline.
        Clears Redis key and updates PostgreSQL last_seen.
        """
        key = PresenceRepository._redis_key(user_id)

        try:
            r = _get_redis()
            # Keep the key briefly with last_seen for grace period reads
            now_iso = timezone.now().isoformat()
            pipe = r.pipeline()
            pipe.hset(key, mapping={"online": "0", "last_seen": now_iso})
            pipe.expire(key, 60)  # Keep for 60s so last_seen can be read
            pipe.execute()
        except redis.RedisError as exc:
            logger.error("Redis error in set_offline for %s: %s", user_id, str(exc))

        try:
            Presence.upsert(user_id=user_id, online=False)
        except Exception as exc:
            logger.error("DB error in set_offline for %s: %s", user_id, str(exc))

    @staticmethod
    def refresh_ttl(user_id: str) -> None:
        """
        Refresh the Redis TTL for an online user (called on heartbeat).
        This is the mechanism that keeps users marked as online.
        If no heartbeat arrives within CHAT_PRESENCE_TTL_SECONDS, the key expires
        and the user is automatically treated as offline.
        """
        key = PresenceRepository._redis_key(user_id)
        ttl = settings.CHAT_PRESENCE_TTL_SECONDS
        now_iso = timezone.now().isoformat()

        try:
            r = _get_redis()
            # Only refresh if the key exists and user is still marked online
            if r.exists(key):
                pipe = r.pipeline()
                pipe.hset(key, "last_seen", now_iso)
                pipe.expire(key, ttl)
                pipe.execute()
        except redis.RedisError as exc:
            logger.error("Redis error in refresh_ttl for %s: %s", user_id, str(exc))

    @staticmethod
    def get_presence(user_id: str) -> dict:
        """
        Get the current presence state for a user.

        Returns:
            {
                "user_id": str,
                "online": bool,
                "last_seen": str (ISO datetime)
            }

        Falls back to PostgreSQL if Redis key is missing.
        """
        key = PresenceRepository._redis_key(user_id)

        try:
            r = _get_redis()
            data = r.hgetall(key)
            if data:
                return {
                    "user_id": user_id,
                    "online": data.get("online") == "1",
                    "last_seen": data.get("last_seen"),
                }
        except redis.RedisError as exc:
            logger.error("Redis error in get_presence for %s: %s", user_id, str(exc))

        # Fallback to PostgreSQL
        try:
            presence = Presence.objects.get(user_id=user_id)
            return {
                "user_id": user_id,
                "online": False,  # Redis key expired → offline
                "last_seen": presence.last_seen.isoformat(),
            }
        except Presence.DoesNotExist:
            return {
                "user_id": user_id,
                "online": False,
                "last_seen": None,
            }

    @staticmethod
    def is_online(user_id: str) -> bool:
        """Quick check: is this user currently online?"""
        return PresenceRepository.get_presence(user_id).get("online", False)
