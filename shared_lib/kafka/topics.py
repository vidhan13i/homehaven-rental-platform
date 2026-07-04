"""
Kafka Topic Constants
=====================
Single source of truth for all Kafka topic names across all services.
Format: {domain}.{entity}.{event}

Import this in producers and consumers instead of using raw strings
to prevent typos and enable IDE refactoring support.
"""


class Topics:
    # ── Auth Service Events ───────────────────────────────────────────────────
    AUTH_USER_REGISTERED = "auth.user.registered"
    AUTH_USER_LOGGED_IN = "auth.user.logged-in"

    # ── Listings Service Events ───────────────────────────────────────────────
    LISTINGS_LISTING_CREATED = "listings.listing.created"
    LISTINGS_LISTING_UPDATED = "listings.listing.updated"
    LISTINGS_LISTING_DELETED = "listings.listing.deleted"

    # ── Application Service Events ────────────────────────────────────────────
    APPLICATIONS_CREATED = "applications.application.created"
    APPLICATIONS_APPROVED = "applications.application.approved"
    APPLICATIONS_REJECTED = "applications.application.rejected"
    APPLICATIONS_SUBMITTED = "applications.application.submitted"

    # ── Chat Service Events ───────────────────────────────────────────────────
    CHAT_MESSAGE_SENT = "chat.message.sent"
    CHAT_MESSAGE_DELIVERED = "chat.message.delivered"
    CHAT_MESSAGE_SEEN = "chat.message.seen"
    CHAT_CONVERSATION_CREATED = "chat.conversation.created"

    # ── Reviews Service Events ────────────────────────────────────────────────
    REVIEWS_REVIEW_CREATED = "reviews.review.created"
    REVIEWS_REVIEW_UPDATED = "reviews.review.updated"
    REVIEWS_REVIEW_DELETED = "reviews.review.deleted"

    # ── Notification Service Events ───────────────────────────────────────────
    NOTIFICATIONS_CREATED = "notifications.notification.created"
    NOTIFICATIONS_READ = "notifications.notification.read"

    # ── Dead Letter Queue ─────────────────────────────────────────────────────
    DLQ = "dlq.events"

    # ── All Topics (for admin/monitoring) ────────────────────────────────────
    ALL_TOPICS = [
        AUTH_USER_REGISTERED,
        AUTH_USER_LOGGED_IN,
        LISTINGS_LISTING_CREATED,
        LISTINGS_LISTING_UPDATED,
        LISTINGS_LISTING_DELETED,
        APPLICATIONS_CREATED,
        APPLICATIONS_APPROVED,
        APPLICATIONS_REJECTED,
        APPLICATIONS_SUBMITTED,
        CHAT_MESSAGE_SENT,
        CHAT_MESSAGE_DELIVERED,
        CHAT_MESSAGE_SEEN,
        CHAT_CONVERSATION_CREATED,
        REVIEWS_REVIEW_CREATED,
        REVIEWS_REVIEW_UPDATED,
        REVIEWS_REVIEW_DELETED,
        NOTIFICATIONS_CREATED,
        NOTIFICATIONS_READ,
        DLQ,
    ]
