#!/bin/bash
# Setup script for running Aicalling with Podman on Linux

set -e

echo "Setting up Aicalling with Podman..."

# 1. Check prerequisites
if ! command -v podman &> /dev/null; then
    echo "Error: podman is not installed. Please install podman (e.g., dnf install podman / apt install podman)."
    exit 1
fi

COMPOSE_CMD=""
if command -v podman-compose &> /dev/null; then
    COMPOSE_CMD="podman-compose"
elif podman compose version &> /dev/null; then
    COMPOSE_CMD="podman compose"
else
    echo "Error: Neither podman-compose nor 'podman compose' plugin is installed."
    echo "Please install podman-compose (e.g., pip3 install podman-compose)."
    exit 1
fi

# 2. Setup Environment
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please update .env with your specific secrets later."
fi

# 3. Create required directories to avoid root-ownership issues from podman mounting
mkdir -p postgres_data redis_data

# 4. (Optional) SELinux context mapping
# The docker-compose.yml already contains the ':z' flag on volume mounts, 
# which tells Podman to automatically relabel the directory with the correct SELinux context.
# However, if you hit permission denied errors on Linux, you can manually run:
# chcon -Rt svirt_sandbox_file_t .

# 5. Build and run
echo "Building and starting containers using $COMPOSE_CMD..."
$COMPOSE_CMD up --build -d

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "API is running on http://localhost:8000"
echo "Web is running on http://localhost:3000"
echo ""
echo "To view logs, run: $COMPOSE_CMD logs -f"
echo "To stop, run: $COMPOSE_CMD down"
echo "========================================="
