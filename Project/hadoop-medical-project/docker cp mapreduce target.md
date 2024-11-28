# Hadoop K-means Clustering Deployment Guide

## 1. Building the Application
```bash
# Compile the MapReduce JAR file
cd mapreduce
mvn clean package
cd ..

# Copy JAR file to the Hadoop namenode
docker cp mapreduce/target/hadoop-KMeansClusterer-1.0-SNAPSHOT.jar namenode:/KMeans.jar

# Clean up previous output to avoid conflicts
docker exec namenode hadoop fs -rm -r /user/root/heart/output


# Copy input data to the container
docker cp heart.csv namenode:/tmp/heart.csv

# Create HDFS directory structure and upload data
docker exec namenode hadoop fs -mkdir -p /user/root/heart/input
docker exec namenode hadoop fs -put /tmp/heart.csv /user/root/heart/input/


# Remove old results from container
docker exec namenode rm -f /tmp/kmeans_results.csv

# Remove old results from local webapp directory
rm -f ./webapp/kmeans_results.csv



# Run the K-means clustering job
docker exec namenode hadoop jar /KMeans.jar /user/root/heart/input /user/root/heart/output

# Copy results from HDFS to container
docker exec namenode hadoop fs -get /user/root/heart/output/part-r-00000 /tmp/kmeans_results.csv

# Copy results from container to local webapp
docker cp namenode:/tmp/kmeans_results.csv ./webapp/kmeans_results.csv
