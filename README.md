# Reactrine

A scalable, maintainable, and production-ready boilerplate for building modern web applications with React and FastAPI.

"Reactrine" is a portmanteau of **React** and **Doctrine**, reflecting its goal to provide an opinionated, best-practice scaffolding for developers. It enforces proven architectural patterns and includes a comprehensive set of features to accelerate the development of high-quality web applications.

This boilerplate provides a solid foundation for your next project, enforcing best practices from the outset and including a comprehensive set of features to accelerate development. It is designed to be easily understood, extended, and deployed.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Technology Stack

-   **Frontend:** React (with Vite), TypeScript, Material-UI (MUI), React Query, Zustand
-   **Backend:** FastAPI, SQLModel, PostgreSQL
-   **Containerization:** Docker & Docker Compose
-   **Task Runner:** Just

## Features

This boilerplate comes packed with features to get you up and running quickly:

-   **User Authentication:** Secure, cookie-based authentication with email/password and Google OAuth support.
-   **Role-Based Access Control (RBAC):** A simple and extensible RBAC system with default "Admin" and "User" roles.
-   **Admin Management Panel:** A secure area for administrators to manage users, assign roles, and control account statuses.
-   **Personal API Keys (PAKs):** Allow users to generate long-lived API keys for programmatic access.
-   **Integrated LLM Providers:** Pluggable architecture for Large Language Model integration, with built-in support for OpenAI, Amazon Bedrock, and OpenRouter.
-   **Sample Haiku Generator:** A working example of how to leverage the LLM integration to create a feature that generates haikus on demand.
-   **Background Tasks:** Asynchronous task processing with Celery and Redis.
-   **Type-Safe API Client:** Automatically generate a type-safe TypeScript client for your frontend.
-   **Database Migrations:** Manage your database schema with Alembic.
-   **Theming:** A centralized theming system with support for light and dark modes.

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

-   Git, Docker, Node.js, Python 3.11+, and Just.

### Installation

1.  Clone the repo
    ```sh
    git clone https://github.com/your_username_/Project-Name.git
    ```
2.  Set up the environment
    ```sh
    just setup
    ```
3.  Start the development servers
    ```sh
    just start
    ```

For more detailed instructions, see the [Getting Started guide](./docs/getting-started.md).

## Documentation

For more detailed information about the project's architecture, features, and development workflow, please refer to the documentation in the `docs/` directory.

-   [Getting Started](./docs/getting-started.md)
-   [Architecture Overview](./ARCHITECTURE.md)
-   [Project Roadmap](./docs/ROADMAP.md)
-   [Database Management](./docs/database-management.md)
-   [Development Workflow](./docs/development-workflow.md)
-   [Deployment](./docs/deployment.md)
-   [Troubleshooting](./docs/troubleshooting.md)
-   **Features**
    -   [User Authentication](./docs/features/authentication.md)
    -   [Role-Based Access Control (RBAC)](./docs/features/RBAC.md)
    -   [Personal API Keys (PAKs)](./docs/features/personal_api_keys.md)
    -   [Background Tasks](./docs/features/background_tasks.md)
    -   [Type-Safe API Client](./docs/features/api_client_generation.md)
    -   [UI & Theming](./docs/features/ui_and_theming.md)

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please see the [CONTRIBUTING.md](./CONTRIBUTING.md) file for our guidelines.

## License

Distributed under the MIT License. See `LICENSE` for more information.
