# Chat Service

Real-time messaging between tenants and agents. Uses Django Channels with WebSockets for bidirectional communication and includes presence tracking (online/offline status), message rate limiting, and HTML sanitization.

## Why it's a separate service

Chat is fundamentally different from the other services. It runs on Daphne (ASGI) instead of Gunicorn (WSGI) because WebSocket connections are long-lived and need async handling. It also has different scaling needs — a chat server holding 1000 WebSocket connections is a very different workload from an API server handling 1000 short HTTP requests.

## Tech Stack

| Dependency | Why |
|------------|-----|
| Django 6.0.2 | ORM for conversation and message models |
| channels 4.2.2 | Django Channels adds WebSocket protocol support on top of Django |
| channels-redis | Uses Redis as the channel layer backend — this is how messages get broadcast across multiple Daphne workers |
| daphne 4.1.2 | ASGI server that handles both HTTP and WebSocket connections |
| celery 5.4.0 | Background tasks for offline push notifications |
| redis / django-redis | Presence tracking (online/offline TTL keys), Celery broker, channel layer |
| bleach | Sanitizes message content to prevent XSS — users can't inject HTML/JS into messages |
| confluent-kafka | Consumes `ApplicationApproved` events (auto-create conversations), produces `MessageSent` events |
| requests + tenacity | Cross-service calls for permission checking |
| drf-spectacular | API documentation |

## Directory Structure

```
chat_service/
├── chat/
│   ├── models/                    # Conversation, Message models
│   ├── consumers/
│   │   └── chat_consumer.py       # WebSocket consumer (connect, receive, disconnect)
│   ├── services/
│   │   ├── message_service.py     # Message creation with rate limiting
│   │   ├── presence_service.py    # Online/offline tracking via Redis
│   │   ├── notification_service.py # Offline notification dispatch
│   │   ├── conversation_service.py # Conversation CRUD
│   │   └── permission_service.py  # Authorization checks
│   ├── authentication/
│   │   ├── http.py                # JWT auth for REST endpoints
│   │   └── websocket.py           # JWT auth for WebSocket connections
│   ├── api/                       # REST views for conversations and messages
│   └── routing.py                 # WebSocket URL routing
├── config/
│   ├── settings.py
│   ├── asgi.py                    # ASGI config (HTTP + WebSocket routing)
│   └── db_router.py
├── celery_app.py
├── Dockerfile
└── requirements.txt
```

## Key Endpoints

### REST API
| Method | Path | What it does |
|--------|------|-------------|
| GET | `/api/chat/conversations/` | List user's conversations |
| GET | `/api/chat/conversations/{id}/messages/` | Paginated message history |
| POST | `/api/chat/conversations/{id}/messages/` | Send a message (REST fallback) |

### WebSocket
| Protocol | Path | What it does |
|----------|------|-------------|
| WS | `ws://localhost:8000/ws/chat/{conversation_id}/` | Real-time bidirectional messaging |

The WebSocket connection handles:
- Sending and receiving messages in real-time
- Typing indicators
- Online/offline presence updates
- Heartbeat pings to keep connections alive

## How presence tracking works

- When a user connects via WebSocket, a Redis key is set with a TTL (e.g., `presence:user:{id}`)
- The client sends heartbeat pings every N seconds to refresh the TTL
- When the TTL expires (user disconnected or closed browser), they appear offline
- On new connections, the server checks Redis for the other participant's presence status

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret |
| `JWT_SECRET_KEY` | Yes | JWT verification |
| `DB_HOST`, `DB_PORT`, `DB_PASSWORD` | Yes | PostgreSQL connection |
| `REDIS_URL` | No | Cache and presence (defaults to `redis://redis:6379/0`) |
| `CELERY_BROKER_URL` | No | Task queue broker |
| `KAFKA_BOOTSTRAP_SERVERS` | No | Kafka broker address |

## Running Standalone

```bash
docker compose up -d db redis kafka chat_service
```

Chat needs Redis for the channel layer and Kafka for event consumption.

## API Docs

[http://localhost:8007/api/docs/](http://localhost:8007/api/docs/)
