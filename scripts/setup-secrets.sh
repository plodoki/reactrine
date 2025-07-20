#!/bin/bash

# Setup secrets for local development
# This script creates secure random secrets or copies example files as appropriate

set -e

echo "Setting up secrets for local development..."

# Create secrets directory if it doesn't exist
mkdir -p secrets

# Function to generate a secure random password
generate_password() {
    openssl rand -base64 32
}

# Function to create secret file if it doesn't exist
create_secret() {
    local secret_file="$1"
    local content="$2"
    local description="$3"

    if [ ! -f "$secret_file" ]; then
        echo "$content" > "$secret_file"
        echo "✅ Created $secret_file ($description)"
    else
        echo "Secret file $secret_file already exists, skipping..."
    fi
}

# Generate secure random secrets
create_secret "secrets/secret_key.txt" "$(generate_password)" "secure random key for JWT tokens"
create_secret "secrets/session_secret_key.txt" "$(generate_password)" "secure random key for sessions"
create_secret "secrets/postgres_password.txt" "$(generate_password)" "secure random database password"

# Copy example files for secrets that need placeholder values
secrets_from_examples=(
    "openai_api_key.txt"
    "openrouter_api_key.txt"
    "aws_access_key_id.txt"
    "aws_secret_access_key.txt"
    "pip_extra_index_url.txt"
)

for secret_name in "${secrets_from_examples[@]}"; do
    example_file="secrets/${secret_name}.example"
    secret_file="secrets/${secret_name}"

    if [ -f "$example_file" ]; then
        if [ ! -f "$secret_file" ]; then
            cp "$example_file" "$secret_file"
            echo "📋 Created $secret_file from example (needs your actual values)"
        else
            echo "Secret file $secret_file already exists, skipping..."
        fi
    fi
done

echo ""
echo "✅ Secrets setup complete!"
echo ""
echo "🔐 Generated secure random secrets:"
echo "   - secrets/secret_key.txt (JWT token signing)"
echo "   - secrets/session_secret_key.txt (session cookie signing)"
echo "   - secrets/postgres_password.txt (database password)"
echo ""
echo "⚠️  IMPORTANT: Update these files with your actual API credentials:"
echo "   - secrets/openai_api_key.txt (your OpenAI API key)"
echo "   - secrets/openrouter_api_key.txt (your OpenRouter API key)"
echo "   - secrets/aws_access_key_id.txt (your AWS access key)"
echo "   - secrets/aws_secret_access_key.txt (your AWS secret key)"
echo ""
echo "💡 Random secrets are automatically generated and ready for use"
echo "💡 For production, use external secret management (AWS Secrets Manager, Vault, etc.)"
