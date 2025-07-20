# System Architecture

This document describes the high-level architecture of the Reactrine application.

## Overview

The application follows a modular monolithic architecture pattern, meaning all components are deployed together but internally organized in a modular fashion. This allows for easier maintenance and potential future separation into microservices if needed.

## Core Components

### Frontend

- **Framework:** React with TypeScript
- **Build Tool:** Vite
- **UI Components:** Material UI (MUI)
- **State Management:**
  - Local/Component State: React Hooks (`useState`, `useReducer`)
  - Server State/Caching: React Query (TanStack Query)
  - Global State: Zustand (for UI state, theme, sessions)
- **Routing:** React Router v6

The frontend is organized by features, with shared components and utilities. Each feature has its own directory with components, hooks, and services specific to that feature.

### Backend

- **Framework:** FastAPI
- **ORM/Data Modeling:** SQLModel (with Pydantic v2)
- **Database:** PostgreSQL
- **Migrations:** Alembic
- **Background Tasks:** Celery

The backend follows a layered architecture:

- **API Routes:** Entry points for HTTP requests
- **Services:** Business logic implementation
- **Models:** Data models representing database tables
- **Schemas:** Pydantic schemas for request/response validation

### Database

PostgreSQL is used as the primary database with async connections through SQLModel and SQLAlchemy.

### Infrastructure

- **Containerization:** Docker with Docker Compose for local development
- **Development Environment:** VS Code DevContainers
- **CI/CD:** GitHub Actions (configured in `.github/workflows/`)
- **Message Broker:** Redis (for Celery)

## Data Flow

### Typical Request Flow

1. **Client Request:** React frontend sends HTTP request via Axios
2. **API Gateway:** FastAPI receives request at versioned endpoint (`/api/v1/...`)
3. **Middleware Processing:** Request passes through a stack of middlewares:
   - **CORS Handling:** Enforces Cross-Origin Resource Sharing policies.
   - **Trusted Host:** Validates the `Host` header.
   - **Rate Limiting:** Prevents abuse by limiting the number of requests from a single IP.
   - **Request Logging:** Logs incoming requests with a correlation ID for tracing.
   - **Session Management:** Handles user sessions.
   - **Authentication/Authorization:** Verifies user identity and permissions (if required).
4. **Route Handling:** FastAPI routes to appropriate endpoint handler
5. **Dependency Injection:** FastAPI injects dependencies (DB session, current user, etc.)
6. **Business Logic:** Service layer processes the request
7. **Data Access:** Services interact with database through SQLModel/SQLAlchemy
8. **Response Formation:** Pydantic schemas validate and serialize response
9. **Client Processing:** React Query caches response and updates UI

### Haiku Generation Flow (Example)

1. User enters topic in `HaikuGeneratorPage`
2. `useHaikuGenerator` hook triggers mutation
3. `haikuService.generateHaiku()` sends POST to `/api/v1/haiku`
4. Backend `HaikuService` constructs prompt and calls LLM API
5. LLM response is processed and returned as `HaikuResponse`
6. Frontend displays generated haiku with loading/error states

## Key Integrations

### Background Tasks

The application uses Celery with Redis as a message broker to handle long-running background tasks. This allows the API to offload work and respond to clients quickly.

- **Task Definition:** Tasks are defined in the `backend/app/tasks` directory.
- **Worker:** A Celery worker process executes tasks in the background.
- **Monitoring:** Task status can be monitored through the API.

### LLM Service

The application includes an LLM service abstraction that:

- Provides a consistent interface for interacting with LLM APIs
- Handles different model providers through a common API
- Manages error handling, retries, and logging
- Supports structured output through Pydantic models

## Development Workflow

1. Local development using Docker Compose
2. Code quality enforced by pre-commit hooks
3. Testing at multiple levels (unit, integration, E2E)
4. Continuous integration through GitHub Actions

## Scaling Considerations

- The modular structure facilitates future extraction into microservices
- Database connections utilize connection pooling for efficiency
- Stateless API design allows for horizontal scaling
- Environment-specific configurations support different deployment environments

## Security Design

- JWT-based authentication with secure token handling using `python-jose`.
- Password hashing using `passlib`.
- Role-based access control for authorization
- Input validation using Pydantic
- Security headers and CORS protection
- Rate limiting for public endpoints
- Environment variable management for secrets

## Monitoring and Logging

- Structured JSON logging format
- Request correlation IDs for tracing requests
- Health check endpoints for infrastructure monitoring
- Configurable logging levels
