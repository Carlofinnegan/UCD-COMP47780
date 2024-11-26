#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting Heart Analysis Setup..."

# 1. Check prerequisites
echo "📋 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }
command -v mvn >/dev/null 2>&1 || { echo "❌ Maven is required but not installed. Aborting." >&2; exit 1; }

# 2. Build MapReduce Job
echo "🔨 Building MapReduce job..."
cd mapreduce
mvn clean package
cd ..

# 3. Stop any running containers and clean up
echo "🧹 Cleaning up previous deployment..."
docker-compose down -v
docker system prune -f

# 4. Start Hadoop cluster
echo "🐘 Starting Hadoop cluster..."
docker-compose up -d namenode datanode1 resourcemanager nodemanager historyserver

# 5. Wait for services to be ready
echo "⏳ Waiting for Hadoop services to start..."
sleep 30

# 6. Set up HDFS directories
echo "📂 Setting up HDFS directories..."
docker exec namenode bash -c '
    hdfs dfs -rm -r -f /user/root/heart || true
    hdfs dfs -mkdir -p /user/root/heart/input
'

# 7. Upload data
echo "📤 Uploading data to HDFS..."
docker exec namenode bash -c "hdfs dfs -put /tmp/heart.csv /user/root/heart/input/"

# 8. Verify input data
echo "🔍 Verifying input data..."
docker exec namenode bash -c "hdfs dfs -ls /user/root/heart/input"

# 9. Copy and run MapReduce job
echo "📊 Running MapReduce analysis..."
docker cp mapreduce/target/heart-analysis-1.0-SNAPSHOT.jar namenode:/heart-analysis.jar
docker exec namenode bash -c "hadoop jar /heart-analysis.jar com.heartanalysis.HeartAnalysis /user/root/heart/input /user/root/heart/output"

# Print the command output for debugging
echo "🔍 Verifying execution..."
docker exec namenode bash -c "hdfs dfs -ls /user/root/heart/output || true"
docker exec namenode bash -c "hdfs dfs -cat /user/root/heart/output/part-r-00000 || true"

# 10. Start webapp
echo "🌐 Starting web application..."
docker-compose up -d --build webapp

echo "
✨ Setup Complete! ✨

Access points:
- Dashboard: http://localhost:5000
- HDFS UI: http://localhost:9870
- YARN UI: http://localhost:8088

To check HDFS contents:
docker exec namenode bash -c \"hdfs dfs -ls /user/root/heart/input\"

To view MapReduce results:
docker exec namenode bash -c \"hdfs dfs -cat /user/root/heart/output/part-r-00000\"

To view webapp logs:
docker-compose logs -f webapp
"