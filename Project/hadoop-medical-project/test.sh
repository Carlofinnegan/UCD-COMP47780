#!/bin/bash

# test.sh
echo "Testing HDFS setup..."
docker exec -it namenode bash -c "hdfs dfs -ls /user/root"

echo -e "\nTesting web application..."
curl http://localhost:5000/test-hdfs
echo -e "\n"
curl http://localhost:5000/test-file
