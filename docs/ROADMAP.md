# Project Roadmap

This document outlines potential future enhancements for the Reactrine. These are opportunities to make the boilerplate even more powerful and versatile. Contributions are welcome!

## Backend & API Enhancements

#### WebSocket Support for Real-Time Features

- **Suggestion:** Add a `WebSocket` endpoint example (e.g., a simple chat or notification service) and document the setup.
- **Why:** Real-time functionality is increasingly common. Providing a pre-configured WebSocket manager would enable features like live notifications, collaborative editing, or real-time dashboards.

#### General-Purpose Caching Layer

- **Suggestion:** Integrate a Redis-based caching utility (e.g., using `fastapi-cache2`) that can be applied as a decorator to cache expensive, non-user-specific API responses.
- **Why:** A general-purpose response cache can dramatically improve performance for public or semi-public endpoints, reducing database load.

#### Email Sending Service

- **Suggestion:** Add a generic email service that integrates with a provider like Amazon SES or SendGrid. It should be exposed as a service available via dependency injection and have a corresponding Celery task for sending emails asynchronously.
- **Why:** User-facing applications universally need to send emails for registration confirmation, password resets, and notifications. This is a foundational feature.

#### Feature Flag System

- **Suggestion:** Integrate a simple feature flag system, either using a database table or a service like LaunchDarkly.
- **Why:** Feature flags are indispensable for modern development, enabling trunk-based development, A/B testing, and canary releases.

## Frontend Enhancements

#### Internationalization (i18n)

- **Suggestion:** Integrate `react-i18next` and structure the `frontend/src` directory to include a `locales` folder with example translation files.
- **Why:** Building for a global audience often requires multi-language support. A pre-configured i18n setup would save developers significant time.

#### Storybook for Component Development

- **Suggestion:** Add Storybook to the frontend to create a visual library of the MUI components, allowing for isolated component development and testing.
- **Why:** A component library is a best practice for maintaining a consistent UI and provides an interactive, developer-focused tool.

#### Advanced & Standardized Form Handling

- **Suggestion:** Integrate `react-hook-form` with a resolver for a validation library like `zod`. Create a few reusable, styled form components that are already wired up.
- **Why:** Forms are the backbone of most web apps. Standardizing on a powerful library like `react-hook-form` improves performance and simplifies validation.

## DevOps & Observability

#### Distributed Tracing

- **Suggestion:** Integrate OpenTelemetry into both the FastAPI backend and the React frontend.
- **Why:** As applications grow, debugging performance bottlenecks becomes difficult. Distributed tracing provides invaluable visibility into the entire request lifecycle.

#### Metrics & Monitoring

- **Suggestion:** Add Prometheus client libraries to the backend to expose key application metrics (e.g., request latency, error rates) on a `/metrics` endpoint.
- **Why:** Proactive monitoring is key to maintaining a healthy application. Exposing Prometheus metrics is the industry standard.

#### Container Image Vulnerability Scanning

- **Suggestion:** Add a step to the CI/CD pipeline to scan the final Docker images for known vulnerabilities using a tool like `trivy` or `grype`.
- **Why:** This adds a critical layer of security, ensuring that vulnerable dependencies don't make it into production.

## Code Refinement Opportunities

The following are smaller, more specific opportunities for improving the existing codebase:

- **Refactor Redundant Database Checks:** In the user registration endpoint, rely on a `try...except IntegrityError` block instead of checking if a user exists before creation. This is more performant and robust against race conditions.
- **Centralize Cookie Expiration:** Use a single constant for the refresh token expiration time in both the token generation logic and the cookie-setting utility to ensure consistency.
- **Improve OAuth Public Key Handling:** Implement a caching layer for Google's public keys to reduce latency and reliance on Google's endpoint during the OAuth verification process.
- **Simplify Frontend State Management:** Refactor the Zustand store to use a wrapper function for handling loading states, reducing boilerplate and potential errors in async actions.
- **Decouple Services from Axios:** Have the `authService` catch `AxiosError` and re-throw a generic `AuthenticationError` to decouple the state store from the specific HTTP client.
- **Use Generated Types Directly:** Eliminate manual type mapping in the frontend services by importing and using the `User` type directly from the generated API client.
