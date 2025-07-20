# Getting Started

This guide will walk you through the process of setting up the Reactrine for local development.

## Prerequisites

Before you begin, make sure you have the following tools installed on your system:

- Git
- Docker and Docker Compose
- Node.js (LTS version)
- Python 3.11+
- [Just](https://github.com/casey/just) (a command runner)

## Quick Start

Follow these steps to get your development environment up and running:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/Reactrine-boilerplate.git
    cd Reactrine-boilerplate
    ```

2.  **Set up environment and secrets:**

    The project includes a setup script that will help you configure your local environment. This script will automatically copy the example environment files and set up development secrets.

    ```bash
    just setup
    ```

    After running the setup script, you may need to configure your actual secrets in the `secrets/` directory. For more detailed information on secret management, see the [Environment Management guide](ENVIRONMENT_MANAGEMENT.md).

    ```bash
    # Example: Create a database password
    echo "your_postgres_password" > secrets/postgres_password.txt

    # Example: Generate a secure application secret key
    echo "$(openssl rand -base64 32)" > secrets/secret_key.txt
    ```

3.  **Install Git hooks:**

    The project uses pre-commit hooks to ensure code quality. They are installed automatically as part of `just setup`, but you can also install them manually:

    ```bash
    pre-commit install
    ```

4.  **Initialize the database:**

    This command will run the database migrations and set up the initial schema.

    ```bash
    just db-upgrade
    ```

5.  **Start the development environment:**

    This will start all the necessary services, including the backend, frontend, and database, using Docker Compose.

    ```bash
    just start
    ```

6.  **Access the application:**

    Once the services are running, you can access the application at the following URLs:

    - **Frontend:** [http://localhost:3000](http://localhost:3000)
    - **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
    - **Backend Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

## Development Environment Options

### Option 1: Docker Compose (Recommended)

This is the simplest and recommended way to run the application for development. The `just start` command handles everything for you.

```bash
just start  # Starts all services in containers
```

### Option 2: VS Code DevContainer

If you use VS Code, you can use the included DevContainer configuration for a seamless development experience.

1.  Open the project folder in VS Code.
2.  Install the "Remote - Containers" extension.
3.  Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and select "Remote-Containers: Reopen in Container".

### Option 3: Local Development (Without Docker)

If you prefer to run the services directly on your host machine, you can do so with the following commands. Note that for this option, you will need to have a PostgreSQL database and Redis running on your local machine and configure the environment variables accordingly.

```bash
# In one terminal, start the backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start the frontend
cd frontend
npm install
npm run dev
```
