"""
Presence Service.

High-level interface for managing user presence.
Consumers and views call this; presence_repository handles the actual Redis/DB ops.

Provides both sync (for REST API views) and async (for WebSocket consumer) methods.
"""

import logging

from asgiref.sync import sync_to_async

from chat.repositories import PresenceRepository

logger = logging.getLogger("chat.services.presence")


class PresenceService:
    """Business logic for user online/offline status."""

    # ── Sync versions (for REST API views and Celery tasks) ───────────────────

    @staticmethod
    def set_online(user_id: str) -> None:
        """Mark a user as online (WebSocket connected)."""
        logger.info("User %s is now ONLINE", user_id)
        PresenceRepository.set_online(user_id)

    @staticmethod
    def set_offline(user_id: str) -> None:
        """Mark a user as offline (WebSocket disconnected)."""
        logger.info("User %s is now OFFLINE", user_id)
        PresenceRepository.set_offline(user_id)

    @staticmethod
    def refresh(user_id: str) -> None:
        """Refresh presence TTL on heartbeat."""
        PresenceRepository.refresh_ttl(user_id)

    @staticmethod
    def get_presence(user_id: str) -> dict:
        """Return presence dict: {user_id, online, last_seen}."""
        return PresenceRepository.get_presence(user_id)

    @staticmethod
    def is_online(user_id: str) -> bool:
        """Quick online check."""
        return PresenceRepository.is_online(user_id)

    # ── Async versions (for AsyncWebsocketConsumer) ───────────────────────────

    @staticmethod
    async def async_set_online(user_id: str) -> None:
        """Async: mark user online."""
        await sync_to_async(PresenceService.set_online)(user_id)

    @staticmethod
    async def async_set_offline(user_id: str) -> None:
        """Async: mark user offline."""
        await sync_to_async(PresenceService.set_offline)(user_id)

    @staticmethod
    async def async_refresh(user_id: str) -> None:
        """Async: refresh presence TTL."""
        await sync_to_async(PresenceService.refresh)(user_id)

    @staticmethod
    async def async_is_online(user_id: str) -> bool:
        """Async: quick online check."""
        return await sync_to_async(PresenceService.is_online)(user_id)
