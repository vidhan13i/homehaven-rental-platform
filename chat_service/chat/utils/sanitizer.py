"""
Message content sanitization utilities.

Prevents XSS, HTML injection, and other content-based attacks
before any user content is stored or broadcast.

Why bleach?
  - bleach is a whitelist-based HTML sanitizer (not a blacklist).
  - It strips all tags/attributes not explicitly allowed.
  - For plain-text messages, we strip all HTML entirely.
  - For future rich-text support, the allowed_tags whitelist can be extended.
"""

import logging
import re
from typing import Optional

import bleach
from django.conf import settings

logger = logging.getLogger("chat.sanitizer")

# For text messages: strip ALL HTML tags — no HTML allowed in plain text chat
_ALLOWED_TAGS: list[str] = []
_ALLOWED_ATTRIBUTES: dict = {}

# Regex for detecting overly long sequences of whitespace / zero-width characters
_INVISIBLE_CHAR_PATTERN = re.compile(r"[\u200b-\u200f\u202a-\u202e\ufeff\u00ad]+")

# Max message length (configurable per settings)
_MAX_MESSAGE_LENGTH = getattr(settings, "CHAT_MESSAGE_MAX_LENGTH", 4000)


def sanitize_message_content(content: str) -> str:
    """
    Sanitize a plain-text message for safe storage and broadcast.

    Steps:
      1. Strip whitespace from edges
      2. Remove invisible/zero-width characters (used in Unicode attacks)
      3. Strip all HTML tags via bleach (XSS prevention)
      4. Truncate to max length
      5. Reject if empty after sanitization

    Returns the sanitized string (may be empty — caller must validate).
    """
    if not isinstance(content, str):
        return ""

    # 1. Strip leading/trailing whitespace
    content = content.strip()

    # 2. Remove invisible characters
    content = _INVISIBLE_CHAR_PATTERN.sub("", content)

    # 3. Strip all HTML (bleach strips tags, escapes entities)
    content = bleach.clean(
        content,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        strip=True,  # Remove disallowed tags (don't escape them)
        strip_comments=True,
    )

    # 4. Truncate to max length
    if len(content) > _MAX_MESSAGE_LENGTH:
        content = content[:_MAX_MESSAGE_LENGTH]
        logger.warning("Message truncated to %d characters", _MAX_MESSAGE_LENGTH)

    return content


def validate_message_content(content: str) -> Optional[str]:
    """
    Validate a message content string.

    Returns an error string if invalid, None if valid.
    Callers should reject the message if this returns a non-None string.
    """
    if not content or not content.strip():
        return "Message content cannot be empty"

    if len(content) > _MAX_MESSAGE_LENGTH:
        return f"Message too long (max {_MAX_MESSAGE_LENGTH} characters)"

    return None


def validate_message_type(message_type: str) -> bool:
    """Validate that the message_type is a known value."""
    from chat.models.message import Message

    valid_types = [choice[0] for choice in Message.MessageType.choices]
    return message_type in valid_types
