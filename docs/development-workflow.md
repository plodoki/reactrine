
# Development Workflow

This document outlines the typical workflow for developing new features, as well as the tools and commands that help ensure code quality.

## Just Commands

This project uses [Just](https://github.com/casey/just) as a command runner for common development tasks. Here are some of the most frequently used commands:

### Environment Management

-   `just setup`: Install all dependencies and initialize the project for the first time.
-   `just start`: Start the development environment using Docker Compose.
-   `just stop`: Stop the development environment.
-   `just logs`: View the logs of all running containers.
-   `just logs <service>`: View the logs for a specific service (e.g., `just logs backend`).

### Code Quality

-   `just format`: Run all code formatters (Black for Python, Prettier for JS/TS).
-   `just lint`: Run all code linters (Ruff for Python, ESLint for JS/TS).
-   `just typecheck`: Run all type checkers (mypy for backend, tsc for frontend).

### Testing

-   `just test`: Run all tests for both the frontend and backend.
-   `just test-be`: Run only the backend tests (pytest).
-   `just test-fe`: Run only the frontend tests (vitest).

### Database

-   `just db-migrate`: Generate a new database migration based on model changes.
-   `just db-upgrade`: Apply all pending database migrations.

### API Client Generation

-   `just api-client`: Generate the type-safe frontend API client from the backend's OpenAPI spec. (Requires the dev server to be running).

## Git Workflow

We recommend following a standard feature-branch workflow:

1.  **Create a feature branch:**

    ```bash
    git checkout -b feature/your-feature-name
    ```

2.  **Make your changes and commit:**

    Commit your changes using the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification. This helps keep the commit history clean and readable.

    ```bash
    git add .
    git commit -m "feat: add your feature description"
    ```

    Common commit types include:
    -   `feat`: a new feature
    -   `fix`: a bug fix
    -   `docs`: documentation changes
    -   `style`: formatting, white-space changes
    -   `refactor`: code refactoring without changing functionality
    -   `test`: adding or improving tests
    -   `chore`: maintenance tasks, dependency updates

3.  **Run quality checks before pushing:**

    Before you push your changes, make sure they pass all the quality checks:

    ```bash
    just format
    just lint
    just typecheck
    just test
    ```

4.  **Push and create a pull request:**
    ```bash
    git push origin feature/your-feature-name
    ```
    Then, open a pull request on GitHub for review.

## Pre-commit Hooks

The project uses pre-commit hooks to automatically run formatters and linters on your code before you commit it. This helps ensure that all code committed to the repository follows the same style guidelines.

The hooks are configured in the `.pre-commit-config.yaml` file and are installed automatically when you run `just setup`.

If you ever need to run the hooks manually on all files, you can use the following command:

```bash
pre-commit run --all-files
```
