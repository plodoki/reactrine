#!/bin/bash
# setup-env.sh - Script to initialize environment variables for the project

# Exit on error
set -e

echo "Setting up environment variables..."

if [ ! -f "./frontend/.env" ]; then
  cp ./frontend/.env.example ./frontend/.env
  echo "Created frontend .env file"
fi

if [ ! -f "./backend/.env" ]; then
  cp ./backend/.env.example ./backend/.env
  echo "Created backend .env file"
fi

if [ ! -f "./.env" ]; then
  cp ./.env.example ./.env
  echo "Created root .env file"
fi

echo "Environment setup complete!"
echo "You can now run 'docker-compose up' to start the development environment."
