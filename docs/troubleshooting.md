
# Troubleshooting

Here are some common issues you might encounter and how to resolve them:

-   **`just` command not found:**
    -   Ensure you have [Just](https://github.com/casey/just#installation) installed correctly and that its installation directory is in your system's `PATH`.

-   **Docker permission errors (Linux):**
    -   You might need to run Docker commands with `sudo`. Alternatively, you can [add your user to the `docker` group](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user) to avoid needing `sudo` for every command.

-   **Port conflicts (e.g., "port is already allocated"):**
    -   This means another service on your machine is using a port needed by the application (e.g., 3000 for the frontend, 8000 for the backend, or 5432 for PostgreSQL). You can either stop the conflicting service or change the ports in your `config/*.env` files and `docker-compose.override.yml`.

-   **Database connection issues:**
    -   Verify that the PostgreSQL container is running (`docker ps -a | grep postgres`).
    -   Check that your `DATABASE_URL` in your `.env` file is correct for your environment.
    -   Ensure that you have run `just db-upgrade` successfully to initialize the database schema.

-   **Frontend shows errors or backend requests fail:**
    -   Check the browser's developer console for any frontend errors.
    -   Check the container logs with `just logs` for any backend errors.
    -   Ensure your `.env` file is correctly configured, especially API keys or the `VITE_API_BASE_URL` if the frontend needs them.

-   **"Module not found" or similar errors after pulling changes:**
    -   This often means new dependencies have been added. Try re-running `just setup` to install any new packages for the frontend or backend.
    -   If the issue persists, you can try cleaning your Docker images and rebuilding from scratch: `docker compose down -v --rmi all` (warning: this will remove your database volume) and then `just start`.
