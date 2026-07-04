"""
Redis-based sliding window rate limiter for WebSocket messages.

Algorithm: Redis Sorted Set sliding window
  - Key:    rate_limit:{user_id}:messages
  - Score:  Unix timestamp (float) of each message event
  - Value:  Unique event identifier (uuid4)
  - Window: CHAT_RATE_LIMIT_WINDOW_SECONDS seconds
  - Max:    CHAT_RATE_LIMIT_MAX_MESSAGES per window

Why Sorted Set?
  - ZRANGEBYSCORE lets us count events within a sliding time window efficiently.
  - ZREMRANGEBYSCORE removes expired events.
  - The entire check-and-add is done in a Lua script for atomicity.
  - O(log N) per operation.

Why in the service layer (not consumer)?
  - Consumers should not contain business logic.
  - Rate limiting is business logic.
  - Services call this utility; consumers call services.
"""
import time
import uuid
import logging
from typing import Optional

import redis
from django.conf import settings

logger = logging.getLogger("chat.rate_limiter")

# Reuse a single Redis client (thread-safe)
_redis_client: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    """Return a singleton Redis client (lazy initialization)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    return _redis_client


# Lua script for atomic sliding-window rate limit check-and-record.
# Returns 1 if the request is allowed, 0 if rate-limited.
_RATE_LIMIT_SCRIPT = """
local key    = KEYS[1]
local now    = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit  = tonumber(ARGV[3])
local event  = ARGV[4]

-- Remove events outside the current window
redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)

-- Count remaining events in the window
local count = redis.call('ZCARD', key)

if count < limit then
    -- Add this event to the window
    redis.call('ZADD', key, now, event)
    -- Set TTL so the key auto-expires (no stale keys)
    redis.call('EXPIRE', key, window + 1)
    return 1
else
    return 0
end
"""


class MessageRateLimiter:
    """
    Sliding-window rate limiter for chat messages.

    Usage:
        limiter = MessageRateLimiter()
        if not limiter.is_allowed(user_id="abc"):
            # reject message
    """

    def __init__(
        self,
        max_messages: int = None,
        window_seconds: int = None,
    ):
        self.max_messages = max_messages or settings.CHAT_RATE_LIMIT_MAX_MESSAGES
        self.window_seconds = window_seconds or settings.CHAT_RATE_LIMIT_WINDOW_SECONDS

    def is_allowed(self, user_id: str) -> bool:
        """
        Check whether the user is within the rate limit.

        Returns True if the message is allowed, False if rate-limited.
        On Redis failure, defaults to allowing the message (fail-open)
        to avoid blocking legitimate users during infrastructure issues.
        """
        key = f"rate_limit:{user_id}:messages"
        now = time.time()
        event_id = str(uuid.uuid4())

        try:
            r = _get_redis()
            result = r.eval(
                _RATE_LIMIT_SCRIPT,
                1,  # number of keys
                key,
                str(now),
                str(self.window_seconds),
                str(self.max_messages),
                event_id,
            )
            allowed = bool(result)
            if not allowed:
                logger.warning(
                    "Rate limit exceeded for user %s: >%d messages in %ds",
                    user_id,
                    self.max_messages,
                    self.window_seconds,
                )
            return allowed
        except redis.RedisError as exc:
            # Fail-open: don't block users if Redis is temporarily unavailable
            logger.error("Rate limiter Redis error (fail-open): %s", str(exc))
            return True

    def get_remaining(self, user_id: str) -> int:
        """Return the number of messages remaining in the current window."""
        key = f"rate_limit:{user_id}:messages"
        now = time.time()
        try:
            r = _get_redis()
            r.zremrangebyscore(key, "-inf", now - self.window_seconds)
            count = r.zcard(key)
            return max(0, self.max_messages - count)
        except redis.RedisError:
            return self.max_messages
