
# Deployment

This guide covers the process of building and deploying your application to production environments.

## Building for Production

The `just build` command prepares your application for deployment by building the optimized frontend assets and creating production-ready Docker images.

```bash
just build
```

## General Deployment Steps

1.  **Build Images:** Run `just build` to create the production Docker images for the frontend and backend.

2.  **Tag and Push Images:** Tag your generated Docker images and push them to a container registry like Docker Hub, AWS ECR, or Google Artifact Registry.

    ```bash
    # Find your local image IDs
    docker images

    # Tag the images
    docker tag <local_frontend_image_id> your-registry/your-frontend-image:latest
    docker tag <local_backend_image_id> your-registry/your-backend-image:latest

    # Push the images
    docker push your-registry/your-frontend-image:latest
    docker push your-registry/your-backend-image:latest
    ```

3.  **Configure Environment:** Ensure your production environment is configured with all necessary environment variables. This should be done securely, for example, using secrets management tools provided by your cloud provider. Do not commit production secrets to your git repository.

4.  **Run Database Migrations:** Before starting the new version of your application, you must run any pending database migrations against your production database.

    ```bash
    # Example of running migrations in a production container
    docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
    ```

5.  **Deploy:** Deploy the new images to your chosen hosting platform. This could be:
    -   **Cloud Platforms:** AWS (ECS, EKS, App Runner), Google Cloud (Cloud Run, GKE), Azure (Container Apps, AKS), etc. These platforms offer scalable and managed container hosting.
    -   **Kubernetes:** Deploy using Helm charts or Kubernetes manifests.
    -   **Single Server:** For simpler setups, you can use `docker-compose` with the production configuration file.
        ```bash
        docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        ```

Refer to the `ARCHITECTURE.md` for more details on the system's architecture which might influence your deployment strategy.

## Raspberry Pi Deployment

This project includes a streamlined process for deploying the application to a Raspberry Pi.

### Prerequisites

-   A Raspberry Pi with Docker, Docker Compose, `git`, and `just` installed.
-   You have cloned the repository to your Raspberry Pi.
-   You have created and populated the necessary files in the `secrets/` directory on the Raspberry Pi as described in the "Setup" section.

### Deployment Command

Once you have SSH'd into your Raspberry Pi and are in the project's root directory, simply run the following command:

```bash
just deploy-pi
```

This single command will:

1.  Pull the latest changes from the git repository.
2.  Generate the RSA keypair for Personal API Keys (if not already present).
3.  Generate the necessary self-signed SSL certificates for the reverse proxy.
4.  Build the production Docker images.
5.  Apply any pending database migrations.
6.  Start the entire application stack.

Your application will then be available at `https://<your-raspberry-pi-ip>`.
