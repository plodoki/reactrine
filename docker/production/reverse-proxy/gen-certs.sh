
#!/bin/bash

# Create a self-signed certificate for the reverse proxy

# Exit immediately if a command exits with a non-zero status.
set -e

# Create the certificate directory if it doesn't exist
mkdir -p certs

# Generate the certificate and key
openssl req -x509 -newkey rsa:4096 -keyout certs/privkey.pem -out certs/fullchain.pem -sha256 -days 365 -nodes -subj "/C=US/ST=California/L=San Francisco/O=FastStack/OU=Development/CN=localhost"

echo "✅ Self-signed certificates generated successfully in the certs directory."
