#!/bin/bash

# setup.sh
echo "Starting Hadoop cluster..."
docker-compose down -v  # Clean start
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 20

# Initialize HDFS directories and upload data
echo "Initializing HDFS..."
docker exec -it namenode bash -c "hdfs dfs -mkdir -p /user/root && hdfs dfs -put /tmp/heart.csv /user/root/"

# Verify the upload
echo "Verifying HDFS setup..."
docker exec -it namenode bash -c "hdfs dfs -ls /user/root"

echo "Setup complete!"
