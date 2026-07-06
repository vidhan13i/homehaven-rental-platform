# Nginx API Gateway

Single entry point for the entire platform. All client requests hit Nginx on port 8000, which routes them to the appropriate backend service based on URL prefix.

## Why Nginx?

We needed a reverse proxy that could handle routing, CORS, WebSocket upgrades, and static file serving without adding another application-level service. Nginx is battle-tested for this — it's fast, uses minimal memory, and the config is straightforward. The alternative was building a custom API gateway in Django or Flask, but that's unnecessary complexity for URL-prefix routing.

## How routing works

Nginx matches the request URL prefix and proxies to the internal Docker service:

| URL Prefix | Backend Service |
|------------|----------------|
| `/api/auth/` | `auth_service:8000` |
| `/api/profiles/` | `profile_service:8000` |
| `/api/listings/` | `listings_service:8000` |
| `/api/buildings/` | `building_service:8000` |
| `/api/applications/` | `application_service:8000` |
| `/api/reviews/` | `reviews_service:8000` |
| `/api/chat/` | `chat_service:8000` |
| `/api/notifications/` | `notification_service:8000` |
| `/ws/chat/` | `chat_service:8000` (WebSocket upgrade) |
| `/ws/notifications/` | `notification_service:8000` (WebSocket upgrade) |
| `/admin/<service>/` | Each service's Django admin |

## WebSocket support

For WebSocket routes (`/ws/`), Nginx adds the `Upgrade` and `Connection` headers to enable the HTTP → WebSocket protocol upgrade. Without these, the browser's WebSocket handshake would fail silently.

## Files

```
gateway/
├── nginx.conf     # Full routing configuration
└── Dockerfile     # Based on nginx:alpine
```

## Health check

`GET http://localhost:8000/health/` returns `200 OK` if Nginx is running. This is used by Docker Compose healthchecks.

## Local access

The gateway is exposed on port `8000`. All backend services are also exposed on their own ports (8001-8008) for direct access during development, but in production you'd only expose the gateway.
