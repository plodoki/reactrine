# Personal API Keys (PAKs)

The Reactrine includes a secure and robust system for Personal API Keys (PAKs). This allows users to generate long-lived tokens for programmatic access to the API, which is ideal for scripts, third-party integrations, and other automated workflows.

## Core Concepts

- **Long-Lived Tokens:** Unlike standard session tokens that expire quickly, PAKs can be configured with a longer lifespan (from 1 to 90 days), making them suitable for services that need persistent access.
- **Self-Service:** Users can manage their own API keys directly from their profile page, including generating new keys, viewing existing ones, and revoking them at any time.
- **Secure by Design:** The system is built with security as a top priority, incorporating several best practices to protect user accounts and data.

## Security Features

- **RS256 JWTs:** PAKs are signed using the RS256 cryptographic algorithm with a dedicated RSA keypair. This is a stronger algorithm than the one used for standard session tokens and allows the keys for PAKs to be rotated independently of the main application secret key.
- **Secure Storage:** The full JWT is only ever shown to the user once upon creation. The backend stores a SHA-256 hash of the token, not the token itself. This means that even if the database is compromised, the keys cannot be stolen.
- **Server-Side Revocation:** When a user revokes a key, the change is recorded on the server. The system will immediately stop accepting the revoked key for authentication, with a propagation time of less than 60 seconds.
- **Constant-Time Hash Comparison:** When validating a token, the backend uses a constant-time comparison algorithm (`secrets.compare_digest`) to prevent timing attacks.
- **Rate Limiting:** API requests made with a PAK are subject to their own rate-limiting buckets, separate from the rate limits applied to browser-based user sessions.

## How It Works

1.  **Key Generation:** A user navigates to the "API Keys" section of their profile and generates a new key, providing an optional label and expiration date.
2.  **Token Issuance:** The backend creates a new JWT with a unique ID (`jti`), signs it with the private RSA key, and stores a hash of the token in the `api_key` database table.
3.  **Client-Side Usage:** The user copies the generated token and includes it in the `Authorization` header of their API requests as a Bearer token:
    ```
    Authorization: Bearer <your_personal_api_key>
    ```
4.  **Backend Verification:** When the backend receives a request with a PAK, it:
    a. Verifies the JWT signature using the public RSA key.
    b. Extracts the unique ID (`jti`) from the token.
    c. Looks up the corresponding token hash in the database.
    d. Ensures the key has not been revoked or expired.
    e. If all checks pass, the user is authenticated, and the request is processed.

## API Key Management

Users can manage their API keys through a dedicated set of endpoints. These endpoints themselves require a valid, browser-based session (i.e., you must be logged in to the web UI to manage your keys).

- `GET /api/v1/users/me/api-keys`: List all of the user's active API keys.
- `POST /api/v1/users/me/api-keys`: Create a new API key.
- `DELETE /api/v1/users/me/api-keys/{key_id}`: Revoke an existing API key.

This system provides a secure and user-friendly way to enable programmatic access to your application, empowering developers to build powerful integrations and automations.
