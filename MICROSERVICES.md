# HomeHaven Microservices Architecture

The HomeHaven Rental Platform is built using a decoupled, event-driven microservices architecture. The backend is split into 8 independent Django REST Framework (DRF) services, communicating asynchronously via Apache Kafka and synchronously via Nginx API Gateway.

## 1. Auth Service
**Port:** `8001`  
**Purpose:** Handles user registration, authentication, JWT token generation, and password management.  
**Key Features:**
- Issues and verifies JSON Web Tokens (JWT).
- Triggers Kafka `UserRegistered` events.
- Validates OTP status with the Profile Service during login.

## 2. Profile Service
**Port:** `8002`  
**Purpose:** Manages user profiles, identities, and email verification.  
**Key Features:**
- Stores core profile data (first name, last name, DOB, gender).
- Manages Email Verification via OTP (One Time Passwords).
- Dispatches Celery tasks to send verification emails asynchronously.

## 3. Listings Service
**Port:** `8003`  
**Purpose:** Manages the core domain of properties, buildings, units, and real estate agents.  
**Key Features:**
- Full CRUD for properties available for rent.
- Search and filtering for available units.
- Manages property images and agent portfolios.
- Produces `ListingCreated` events on Kafka.

## 4. Building Service
**Port:** `8004`  
**Purpose:** Manages physical building infrastructure, amenities, and geographical locations.  
**Key Features:**
- Tracks building metadata (address, floors, amenities like gym/pool).
- Aggregates building-wide statistics and metrics.

## 5. Application Service
**Port:** `8005`  
**Purpose:** Handles the rental application lifecycle.  
**Key Features:**
- Allows users to submit rental applications for specific units.
- Agents can approve, reject, or place applications on hold.
- Produces `ApplicationCreated`, `ApplicationApproved`, and `ApplicationRejected` events on Kafka to trigger notifications and automated workflows.

## 6. Reviews Service
**Port:** `8006`  
**Purpose:** Manages crowdsourced tenant reviews and ratings for buildings and agents.  
**Key Features:**
- Users can submit reviews and 5-star ratings.
- Aggregates average ratings for buildings and agents.
- Produces `ReviewCreated` events on Kafka.

## 7. Chat Service
**Port:** `8007`  
**Purpose:** Provides real-time messaging between renters and agents.  
**Key Features:**
- Exposes WebSocket endpoints `ws://localhost:8000/ws/chat/` for real-time bidirectional communication.
- Consumes `ApplicationApproved` Kafka events to automatically provision new chat rooms between the applicant and the listing agent.
- Produces `MessageSent` events to trigger offline push notifications.

## 8. Notification Service
**Port:** `8008`  
**Purpose:** A fully decoupled event sink that handles all system notifications (in-app, email, and WebSockets).  
**Key Features:**
- Consumes almost all domain events from Kafka (`UserRegistered`, `ApplicationApproved`, `MessageSent`, etc.).
- Dispatches real-time WebSocket alerts to online users via `ws://localhost:8000/ws/notifications/`.
- Dispatches asynchronous emails via Celery.
- Persists a history of notifications for users to read later.

---

### Accessing the API Documentation
Every single service exposes its own OpenAPI 3.0 documentation. You can view the interactive Swagger UI for any service by visiting:
`http://localhost:<PORT>/api/docs/`
