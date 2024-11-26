
#compile jar if we change it
cd mapreduce
mvn clean package
cd ..


#Move it to hdfs
docker cp mapreduce/target/hadoop-KMeansClusterer-1.0-SNAPSHOT.jar namenode:/KMeans.jar



# First remove old output directory if it exists
docker exec namenode hadoop fs -rm -r /user/root/heart/output

# creat csv in input folder

docker cp heart.csv namenode:/tmp/heart.csv






# make directory and move heart csv tio directory
docker exec namenode hadoop fs -mkdir -p /user/root/heart/input
docker exec namenode hadoop fs -put /tmp/heart.csv /user/root/heart/input/


# First, remove the old file in the container (if it exists)
docker exec namenode rm -f /tmp/kmeans_results.csv

# Then remove the old file in your local webapp directory (if it exists)
rm -f ./webapp/kmeans_results.csv

# execute map reude job


docker exec namenode hadoop jar /KMeans.jar /user/root/heart/input /user/root/heart/output


# copy the stuff accross
docker exec namenode hadoop fs -get /user/root/heart/output/part-r-00000 /tmp/kmeans_results.csv

docker cp namenode:/tmp/kmeans_results.csv ./webapp/kmeans_results.csv





