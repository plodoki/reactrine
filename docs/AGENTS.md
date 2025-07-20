# AGENTS.md

> **Role** This file is the system prompt and guard rails for Gemini or Cursor based code agents. All rules below are non‑negotiable.

## 1. Stack Overview

- **Backend:** FastAPI → SQLAlchemy → Postgres (Docker Compose)
- **Frontend:** React 18 + Vite; served by Nginx (`web` container)
- **Tooling:** `just` recipes, GitHub Actions (lint, test, build)

## 2. Guard‑Rails

1. Code must **compile, lint** (`ruff`, `mypy`, `eslint`), **format** (`black`, `isort`, `prettier`) _and_ **pass tests** before commit.
2. Use SQLAlchemy query builder—no raw SQL.
3. React components are functional only.
4. Secrets via env vars.
5. Add type hints to new Python.
6. React Query for state (no Redux).
7. Use shared API client `@/lib/api`.
8. Keep TS types = Pydantic schemas.
9. Cookie‑based auth + CSRF.
10. FastAPI URLs end with `/`.

## 3. Commands

| Gate           | `just`       |
| -------------- | ------------ |
| Setup          | `setup`      |
| Lint           | `lint`       |
| Test           | `test`       |
| Typecheck      | `typecheck`  |
| Format         | `format`     |
| DB migrate     | `db-migrate` |
| DB upgrade     | `db-upgrade` |
| API client gen | `api-client` |

Agents **run** `just lint`, `just typecheck`, `just format`, and `just test`; abort if any fails.

## 4. Architecture Patterns

### Service Layer Architecture

- **Thin Controllers:** Endpoints delegate to services—no business logic, database queries, or complex validation in endpoints
- **Service Responsibility:** Encapsulate business logic, handle database operations, convert errors to HTTP exceptions
- **Dependency Injection:** Use `Depends()` for service layer injection with singleton pattern for stateless services
- **Repository Pattern:** Use `BaseRepository[T]` with common CRUD operations; domain-specific repositories inherit from base

### Service Instance Management & Caching

- **Singleton Services:** Create singleton instances for stateless services (OAuth, ApiKey, LLMSettings)
- **Factory Functions:** Use factory functions for services that need configuration or database access
- **Service Caching:** Cache expensive service instances (LLM clients, external API clients) with TTL-based expiration
- **Cache Implementation:** Store `(service_instance, cached_at)` tuples; 15 minutes TTL for services, 5 minutes for settings
- **Thread Safety:** Use `asyncio.Lock()` for cache synchronization and double-checked locking for singletons
- **Cache Key Generation:** Create deterministic keys from configuration parameters (provider|model|config_params)
- **Avoid Per-Request Creation:** Never create new service instances on every request for stateless services
- **Database Settings Cache:** Separate cache for database settings lookup to avoid DB hits on every request

### Repository Layer Design

- **Single Responsibility:** Each repository manages one entity type
- **Error Encapsulation:** Handle SQLAlchemy errors within repository layer
- **Method Naming:** Use clear, descriptive names (e.g., `get_by_email`, `get_active_by_user_id`)
- **Constructor Injection:** Initialize repositories in service constructors

### API Client Generation

- **Generated Client Integration:** Use `just api-client` to generate type-safe TypeScript client from OpenAPI spec
- **Configuration Management:** Configure generated client with same base URL and credentials as existing API
- **Environment-Aware URLs:** Use `import.meta.env.VITE_API_BASE_URL` for base URL, not hardcoded values
- **Gradual Migration:** Integrate generated client alongside existing handcrafted services, not as replacement
- **Generated Code Exclusion:** Always add `src/lib/api-client/` to `.gitignore` - never commit generated code
- **Consistent Patterns:** Use generated client for new features while maintaining existing service patterns
- **CSRF Token Support:** Configure generated client to include CSRF tokens for state-changing requests
- **Error Handling:** Apply same error handling patterns to generated client as handcrafted services
- **Type Safety:** Leverage generated TypeScript types for compile-time API contract validation
- **Development Workflow:** Regenerate client after backend API changes during development

## 5. Testing Standards

### Core Testing Principles & Tools

- **Backend:** `pytest`, `pytest-asyncio`; **Frontend:** `vitest`, `@testing-library/react`
- Coverage targets: Backend ≥90%, Frontend ≥80%; Red‑green‑refactor loop
- Async SQLAlchemy mocking: sync methods `Mock`, async methods `AsyncMock`

### Test Isolation & Database Strategy

- **No Global State:** Each test must have its own isolated mock database instance
- **Clean Fixtures:** Use proper pytest fixtures with setup/teardown, not global reset functions
- **Mock Database Pattern:**
  - Unit tests: `create_mock_db_session()` for isolated instances
  - Integration tests: `create_persistent_mock_db_session()` for data persistence across HTTP requests
  - SELECT parsing with WHERE clause filtering and parameter binding support
  - Model filtering and constraint simulation with `IntegrityError`
- **Mock Utilities:** Database mocks in `app/tests/mocks/database.py`, user mocks in `app/tests/mocks/users.py`

### Frontend Testing Architecture

#### Test Organization Structure

- **Service Layer Tests:** Unit tests for API services in `services/__tests__/` with comprehensive mock factories
- **Hook Tests:** Custom React hooks in `hooks/__tests__/` and feature-specific `hooks/__tests__/` directories
- **Component Tests:** React components in `components/__tests__/` with @testing-library/react
- **Integration Tests:** End-to-end workflows in `__tests__/integration/` directories
- **Store Tests:** Zustand stores in `stores/__tests__/` with state management verification
- **Provider Tests:** React context providers in `providers/__tests__/` with lifecycle testing

#### Mock Strategy & Configuration

- **Vitest Configuration:** Ensure `globals: true` in vitest config and `"types": ["vitest/globals"]` in tsconfig
- **Test Setup:** Use `globalThis` for global mocks instead of `global` for cross-platform compatibility
- **Module-Level Mocking:** Use `vi.mock()` at module level for external dependencies (axios, services)
- **Mock Factories:** Create typed mock factories in `test/factories.ts` for consistent test data
- **Service Mocking:** Mock services where imported, not at definition location
- **State Management:** Use `vi.mocked()` for proper TypeScript support in mock assertions
- **Async Behavior:** Control promise resolution/rejection for testing loading states and error handling
- **Test Isolation:** Reset mocks in `beforeEach` hooks to prevent test interference
- **Generated Client Mocks:** Mock generated API clients at module level using `vi.mock()` with proper typing
- **Axios Error Mocking:** Use `InternalAxiosRequestConfig` for axios error response configuration

#### Coverage Requirements & Testing Standards

- **Service Layer:** ≥90% coverage for API services with success/error scenarios
- **Custom Hooks:** ≥85% coverage for React hooks with state transitions
- **Components:** ≥80% coverage for React components with user interactions
- **Stores:** ≥90% coverage for state management with async actions
- **Providers:** ≥75% coverage for context providers with lifecycle events
- **Integration:** ≥70% coverage for end-to-end workflows
- **Mock Assertions:** Always verify mock calls with expected parameters
- **Complete Coverage:** Test both success paths and parameter validation
- **External Services:** Capture initialization parameters to verify credentials
- **Dependency Injection:** Override FastAPI dependencies for consistent mocking

## 6. Error Handling & Security

### Exception Handling Requirements

- **Specific Exceptions:** Catch specific exceptions, not bare `except Exception:`
  - **Database:** `SQLAlchemyError`, `IntegrityError`, `DataError`, `ConnectionError`
  - **External APIs:** `ConnectionError`, `TimeoutError`, `HTTPStatusError`, `httpx.RequestError`, `httpx.HTTPStatusError`
  - **LLM Services:** `LLMConfigurationError`, `LLMGenerationError`, `LLMRateLimitError`, `APIError`, `RateLimitError`
  - **Validation:** `ValueError`, `ValidationError`, `TypeError`, `KeyError`
  - **File Operations:** `FileNotFoundError`, `PermissionError`, `OSError`
- **Exception Hierarchy:** Re-raise custom exceptions without modification
- **Exception Chaining:** Always use `from e` when re-raising exceptions to preserve stack traces
- **Structured Logging:** Log all application events (info, debug, errors) with context. Do not use `print()` statements in application code.
- **User-Safe Messages:** Never expose internal error details; provide user-friendly messages
- **Database Errors:** Use `handle_database_error` utility for consistent handling with rollback
- **Security Context:** In security/auth and middleware code, broad exception handling is acceptable to prevent information leakage

### Centralized Error Handling

- **Use Error Handling Decorators:** Leverage `@with_error_handling()`, `@with_database_error_handling()`, `@with_network_error_handling()` decorators
- **Centralized Error Mapping:** Use `ErrorMapping` class for consistent HTTP status codes and messages
- **Structured Error Logging:** Use `log_error_with_context()` for consistent error logging with context
- **Automatic Exception Conversion:** Use `create_http_exception()` to convert exceptions to HTTPException with proper logging
- **Context-Aware Error Handling:** Include operation descriptions and relevant context in error handling
- **Standardized Status Codes:** Use `ErrorMapping` for consistent HTTP status codes across error types
- **Exception Chaining:** Preserve original exception context with `from e` syntax

### Security & Race Condition Prevention

- **Atomic Operations:** Use database constraints instead of application-level checks
- **IntegrityError Handling:** Catch `IntegrityError` specifically; rollback transactions before re-raising
- **Avoid Check-Then-Create:** Never use `if not exists: create()` patterns
- **Secret Management:** Use environment‑aware fallback: secrets → env vars → test defaults → fail
- **HTTP Tokens:** Never put tokens in URLs; use POST body with form data
- **Input Validation:** Validate all parameters early, especially user IDs and critical inputs

## 7. Performance & Async Best Practices

### Caching in Dependency Injection

- **Avoid Heavy Operations:** Never perform database operations, file I/O, or network calls directly in dependency injection
- **Use Caching Layers:** Implement TTL-based caches for frequently accessed data
- **Lazy Initialization:** Defer expensive operations until actually needed
- **Cache Invalidation:** Provide methods to invalidate cache when configuration changes

### Async Context Best Practices

- **File Operations:** Use environment variables or startup initialization instead of sync file I/O
- **Blocking Operations:** Use `asyncio.to_thread()` for unavoidable sync operations
- **Startup Initialization:** Move heavy operations to application startup hooks

### Performance Metrics Collection

- **Use Timing Decorators:** Apply a timing decorator (`@timing_decorator`) to expensive operations like external API calls (e.g., LLM providers) to log execution time.
- **Consistent Logging:** Ensure performance metrics are logged to the standard logger with a consistent format (e.g., `Performance: {func_name} took {time:.4f} seconds`).
- **Targeted Application:** Apply timing decorators specifically to I/O-bound or CPU-bound operations that are likely to be performance bottlenecks.
- **Decorator Order:** When stacking decorators, place the timing decorator inside other decorators (like retry logic) to measure the execution time of a single attempt.

## 8. Validation & Type Safety

### Pydantic Schema Validation

- **String Fields:** Always include `min_length` and `max_length` constraints
- **Optional Fields:** Use `Optional[str]` with proper None handling in validators
- **Whitespace Handling:** Always trim whitespace and validate against empty strings after trimming
- **Field Validators:** Return cleaned/processed values from validators
- **Numeric Fields:** Include range constraints with `ge` and `le`
- **User-Friendly Messages:** Provide clear, actionable error messages with specific constraints
- **Consistent Tone:** Use consistent language across all validation messages

### Type Hints Requirements

- **Complete Coverage:** All function parameters and return types must have type hints
- **FastAPI Dependencies:** Always include type hints for dependency injection parameters
- **Import Requirements:** Import all necessary types (`User`, `Settings`, `OAuthService`, etc.)
- **Return Types:** Include return type annotations for all functions, including async functions
- **Optional Types:** Use `Optional[T]` or `T | None` for nullable parameters

### Common Type Patterns

- **User Dependencies:** `current_user: User = Depends(get_current_active_user)`
- **Database Sessions:** `db: AsyncSession = Depends(get_db_session)`
- **Settings:** `settings: Settings = Depends(get_settings)`
- **Services:** `service: ServiceType = Depends(get_service_function)`
- **Return Types:** Always specify return types, even for simple functions

### Type Safety Best Practices

- **Mypy Compliance:** All code must pass `mypy --no-incremental backend` without errors
- **Generic Types:** Use proper generic types for collections (`list[str]`, `dict[str, Any]`)
- **Protocol Usage:** Use protocols for interface definitions (e.g., `LLMService`)
- **Type Aliases:** Define type aliases for complex types to improve readability
- **Avoid Any:** Minimize use of `Any` type; prefer specific types or protocols

### Frontend TypeScript Standards

- **Test Types:** Always include `"types": ["vitest/globals"]` in `tsconfig.json` for test environments
- **Global Types:** Use `globalThis` instead of `global` for cross-platform compatibility
- **Axios Types:** Use `InternalAxiosRequestConfig` for axios configuration mocking, not `AxiosRequestConfig`
- **Mock Types:** Define proper interfaces for mock objects rather than using `any`
- **Type Intersections:** Use type intersections for extending global objects: `typeof globalThis & { CustomProp: Type }`
- **React Refresh Compliance:** Add `eslint-disable-next-line react-refresh/only-export-components` for utility functions and constants
- **Test Utilities:** Separate test utilities from components to avoid React refresh warnings
- **Unknown over Any:** Use `unknown` type for generic data instead of `any`
- **Proper Imports:** Import specific types needed for tests (e.g., `InternalAxiosRequestConfig`)
- **Mock Factories:** Create comprehensive mock factories with proper typing for all API responses

## 9. Anti‑Patterns → Fixes (✗/✓)

### Architecture & Performance

- **API:** ✗ multiple axios | ✓ `@/lib/api`
- **API Client:** ✗ hardcoded URLs, commit generated code | ✓ environment-aware config, `.gitignore` generated files
- **Controllers:** ✗ fat endpoints | ✓ thin endpoints + service layer
- **Services:** ✗ god classes, per-request creation | ✓ single‑purpose, singleton pattern + caching
- **Repositories:** ✗ direct SQL in services | ✓ repository pattern
- **Expensive Services:** ✗ recreate LLM clients on every request | ✓ TTL-based instance caching
- **Database Settings:** ✗ query settings on every request | ✓ cache with 5-minute TTL

### Security & Validation

- **Auth:** ✗ mix Bearer/cookies | ✓ cookies + CSRF
- **HTTP Security:** ✗ tokens in URLs | ✓ tokens in POST body
- **Validation:** ✗ missing parameter checks | ✓ validate inputs early
- **Secrets:** ✗ hardcoded defaults | ✓ environment‑aware fallback pattern
- **Race Conditions:** ✗ check-then-create patterns | ✓ atomic operations + IntegrityError handling

### Error Handling & Testing

- **Logging:** ✗ `print()` statements in application code | ✓ structured logging for all events
- **Errors:** ✗ generic exceptions | ✓ specific exceptions + structured logging + exception chaining
- **Error Duplication:** ✗ duplicate error handling patterns | ✓ centralized error handling decorators
- **Error Messages:** ✗ exposing internal details | ✓ user-safe messages with structured logging context
- **Database Errors:** ✗ manual rollback + generic exceptions | ✓ `@with_database_error_handling` decorator
- **Network Errors:** ✗ inconsistent error mapping | ✓ `@with_network_error_handling` decorator
- **Security Exceptions:** ✗ exposing error details | ✓ fail-closed with generic messages
- **Testing:** ✗ incomplete assertions, global mock state | ✓ verify mock calls, per-test mock instances
- **Mock Patching:** ✗ patch at wrong import level | ✓ patch where functions are used
- **Mock Database:** ✗ simple return values | ✓ SQL query parsing with WHERE clause filtering

### Code Quality & Type Safety

- **Schemas:** ✗ mismatched names/types | ✓ exact match
- **FastAPI:** ✗ omit `/` | ✓ include `/`
- **Thread Safety:** ✗ bare singletons | ✓ double‑checked locking
- **Code Structure:** ✗ if/elif chains | ✓ dictionary mapping patterns
- **Method Naming:** ✗ misleading function names | ✓ names match actual behavior
- **Imports:** ✗ type ignore for known issues | ✓ fix root cause + proper imports
- **Type Hints:** ✗ missing parameter/return types | ✓ complete type annotations for all functions

### Frontend Testing & Quality

- **Test Isolation:** ✗ global mock state, shared test data | ✓ reset mocks in `beforeEach`, isolated test instances
- **Async Testing:** ✗ not waiting for async operations | ✓ use `vi.waitFor()` and `act()` for state updates
- **Mock Strategy:** ✗ mocking at definition location | ✓ mock where functions are imported/used
- **Coverage Gaps:** ✗ only testing success paths | ✓ test both success and error scenarios
- **Type Safety:** ✗ `any` types in mock objects | ✓ proper interfaces for all mock data
- **Test Organization:** ✗ mixing test types in same file | ✓ separate unit/integration/component tests
- **Mock Completeness:** ✗ partial mock objects | ✓ comprehensive mock factories matching generated types
- **Store Testing:** ✗ testing implementation details | ✓ testing state transitions and user interactions
- **Any Types:** ✗ using `any` for generic data | ✓ use `unknown` or specific types
- **Global Objects:** ✗ using `global` directly | ✓ use `globalThis` with proper type intersections
- **React Refresh:** ✗ exporting utilities from component files | ✓ add eslint-disable comments or separate files
- **Test Configuration:** ✗ missing test types in tsconfig | ✓ include `"types": ["vitest/globals"]`
- **Axios Mocking:** ✗ using wrong axios types | ✓ use `InternalAxiosRequestConfig` for mocks
- **Mock Factories:** ✗ incomplete mock objects | ✓ comprehensive typed mock factories
- **Import Order:** ✗ mixing imports and mocks | ✓ proper import organization with mocks first

## 10. Workflow & Development

### Code Quality Workflow

- **Lint First:** Run `just lint` before committing; fix all errors and warnings immediately
- **Type Check:** Run `just typecheck` to catch TypeScript issues early
- **Test Coverage:** Maintain ≥90% test coverage; write tests before implementing features
- **Mock Strategy:** Create comprehensive mock factories before writing service tests
- **Import Organization:** Organize imports logically (framework → API clients → mocks → utilities)
- **Type Safety:** Use specific types over `any`; leverage TypeScript's type system fully
- **Generated Code:** Never commit generated API client code; always regenerate after backend changes

### Development Best Practices

- Atomic steps: test → code → docs
- Verify schema before UI work
- Test proxy redirects early
- Fix warnings ASAP
- Use centralized error handling decorators for consistent error responses
- Leverage `ErrorMapping` class for standardized HTTP status codes
- Include operation context in error handling for better debugging

### Frontend Testing Workflow

- **Test-First Development:** Write tests before implementing features; use TDD approach
- **Mock Factory Setup:** Create comprehensive mock factories in `test/factories.ts` before writing tests
- **Layer-by-Layer Testing:** Test services → hooks → components → integration in sequence
- **Coverage Verification:** Run `npm test -- --coverage` regularly to maintain ≥80% coverage
- **Parallel Test Development:** Write tests alongside feature implementation, not as afterthought
- **Integration Testing:** Test complete user workflows after unit tests are complete
- **Mock Isolation:** Reset all mocks in `beforeEach` hooks to prevent test interference
- **Type Safety First:** Define proper interfaces for all mock objects and test data

### Common Pitfalls & Debugging

#### TypeScript Configuration Issues

- **Missing Test Types:** Add `"types": ["vitest/globals"]` to tsconfig.json when test globals are not recognized
- **Global Object Errors:** Use `globalThis` instead of `global` for cross-platform compatibility
- **Axios Type Mismatches:** Use `InternalAxiosRequestConfig` for axios mocking, not `AxiosRequestConfig`
- **Generated Type Mismatches:** Ensure mock factories include all required properties from generated types

#### ESLint & React Refresh Issues

- **Utility Export Warnings:** Add `eslint-disable-next-line react-refresh/only-export-components` for non-component exports
- **Test Utility Conflicts:** Separate test utilities from component files to avoid React refresh warnings
- **Any Type Errors:** Replace `any` with `unknown` for generic data or specific types when known

#### Test Configuration Problems

- **Mock Import Order:** Import test framework functions before API clients to avoid hoisting issues
- **Mock Factory Completeness:** Ensure all mock objects match the structure of generated types
- **Test Isolation:** Use proper mock clearing in `beforeEach` hooks to avoid test interference
- **Coverage Gaps:** Write tests for both success and error scenarios for complete coverage

#### Debugging Strategies

- **Lint Errors:** Run `npm run lint` to catch ESLint issues; fix immediately
- **Type Errors:** Run `npx tsc --noEmit` to catch TypeScript issues without compilation
- **Test Failures:** Use `npm test -- --run` to run tests without watch mode for CI/CD
- **Coverage Analysis:** Use `npm test -- --coverage` to identify untested code paths
- **Mock Debugging:** Verify mock calls with `expect(mockFunction).toHaveBeenCalledWith(expectedArgs)`

## 11. Docs

See `README.md`, `backend/` & `frontend/` READMEs.
