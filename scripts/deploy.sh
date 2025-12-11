#!/bin/bash

# Exit on error
set -e

# Check if environment argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <environment>"
    echo "Example: $0 dev"
    exit 1
fi

ENV=$1
ENV_FILE=".env.${ENV}"

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Configuration file $ENV_FILE not found!"
    exit 1
fi

echo "Loading configuration from $ENV_FILE..."
# Load environment variables
set -a
source "$ENV_FILE"
set +a

# Define image names
API_IMAGE_NAME="anmei-smart-api:${ENV}"
WEB_IMAGE_NAME="anmei-smart-web:${ENV}"

echo "=========================================="
echo "Starting deployment for environment: $ENV"
echo "API Image: $API_IMAGE_NAME"
echo "Web Image: $WEB_IMAGE_NAME"
echo "=========================================="

# Build API
echo "Building API image..."
docker build -t "$API_IMAGE_NAME" -f api/Dockerfile api/

# Build Web
echo "Building Web image..."
# Note: passing build args for Next.js build time variables
docker build \
    --build-arg NEXT_PUBLIC_API_URL="$NEXT_PUBLIC_API_URL" \
    --build-arg NEXT_PUBLIC_APP_KEY="$NEXT_PUBLIC_APP_KEY" \
    --build-arg NEXT_PUBLIC_APP_ID="$NEXT_PUBLIC_APP_ID" \
    -t "$WEB_IMAGE_NAME" \
    -f web/Dockerfile web/

# Stop and remove existing containers if running
echo "Stopping old containers..."
docker rm -f "anmei-smart-api-${ENV}" || true
docker rm -f "anmei-smart-web-${ENV}" || true

# Run API
echo "Starting API container..."
docker run -d \
    --name "anmei-smart-api-${ENV}" \
    --restart unless-stopped \
    -p "${API_PORT:-8000}:8000" \
    --env-file "$ENV_FILE" \
    "$API_IMAGE_NAME"

# Run Web
echo "Starting Web container..."
docker run -d \
    --name "anmei-smart-web-${ENV}" \
    --restart unless-stopped \
    -p "${WEB_PORT:-3000}:3000" \
    -e PORT=3000 \
    "$WEB_IMAGE_NAME"

echo "=========================================="
echo "Deployment successful!"
echo "API running on port ${API_PORT:-8000}"
echo "Web running on port ${WEB_PORT:-3000}"
echo "=========================================="

