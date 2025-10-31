#!/bin/bash

# Function to stop and remove a container if it exists
remove_container() {
    CONTAINER_NAME=$1
    if [ "$(docker ps -aq --filter "name=$CONTAINER_NAME")" ]; then
        echo "Stopping and removing $CONTAINER_NAME..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
    else
        echo "$CONTAINER_NAME does not exist. Skipping removal."
    fi
}

# Remove old containers if they exist
remove_container frontend
remove_container backend

# Pull the latest images
echo "Pulling the latest frontend image..."
docker pull jaysharmafm/wg:frontend

echo "Pulling the latest backend image..."
docker pull jaysharmafm/wg:backend

# Run the new containers
echo "Starting the frontend container..."
docker run -p 5173:5173 --name frontend -d jaysharmafm/wg:frontend

echo "Starting the backend container..."
docker run -p 8000:8000 --name backend -d jaysharmafm/wg:backend

echo "Update completed successfully!"
