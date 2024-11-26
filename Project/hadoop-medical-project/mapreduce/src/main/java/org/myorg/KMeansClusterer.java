package org.myorg;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class KMeansClusterer {
    // Point class remains the same
    public static class Point {
        private double[] dimensions;
        
        public Point(String[] values, int expectedDimensions) {
            dimensions = new double[expectedDimensions];
            for (int i = 0; i < expectedDimensions && i < values.length; i++) {
                try {
                    dimensions[i] = Double.parseDouble(values[i].trim());
                } catch (NumberFormatException e) {
                    throw new NumberFormatException("Invalid number format in data: " + values[i]);
                }
            }
        }
        
        public double distance(Point other) {
            int minDim = Math.min(dimensions.length, other.dimensions.length);
            double sum = 0;
            for (int i = 0; i < minDim; i++) {
                sum += Math.pow(dimensions[i] - other.dimensions[i], 2);
            }
            return Math.sqrt(sum);
        }
        
        // Modified toString to ensure consistent formatting
        public String toString() {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < dimensions.length; i++) {
                if (i > 0) sb.append(",");
                if (i == 8 || i == 9) {  // exang and oldpeak columns
                    sb.append(String.format("%.1f", dimensions[i]));
                } else {
                    sb.append(String.format("%.0f", dimensions[i]));
                }
            }
            return sb.toString();
        }
    }
    
    // Mapper remains the same
    public static class KMeansMapper extends Mapper<Object, Text, Text, Text> {
        private List<Point> centroids = new ArrayList<>();
        private boolean isFirstLine = true;
        private int numDimensions;
        
        @Override
        protected void setup(Context context) throws IOException {
            numDimensions = context.getConfiguration().getInt("dimensions", 2);
            String[] centroidStrings = context.getConfiguration().get("centroids").split(";");
            for (String centroidStr : centroidStrings) {
                centroids.add(new Point(centroidStr.split(","), numDimensions));
            }
        }
        
        @Override
        public void map(Object key, Text value, Context context) throws IOException, InterruptedException {
            String line = value.toString();
            
            if (isFirstLine) {
                isFirstLine = false;
                return;
            }
            
            try {
                String[] values = line.split(",");
                Point point = new Point(values, numDimensions);
                
                int nearestCentroid = 0;
                double minDistance = Double.MAX_VALUE;
                
                for (int i = 0; i < centroids.size(); i++) {
                    double distance = point.distance(centroids.get(i));
                    if (distance < minDistance) {
                        minDistance = distance;
                        nearestCentroid = i;
                    }
                }
                
                context.write(new Text(String.valueOf(nearestCentroid)), new Text(point.toString()));
            } catch (Exception e) {
                System.err.println("Skipping invalid data row: " + line + " Error: " + e.getMessage());
            }
        }
    }
    
    public static class KMeansReducer extends Reducer<Text, Text, Text, Text> {
        private int numDimensions;
        private boolean isFirstOutput = true;
        
        @Override
        protected void setup(Context context) throws IOException {
            numDimensions = context.getConfiguration().getInt("dimensions", 2);
        }
        
        @Override
        public void reduce(Text key, Iterable<Text> values, Context context) 
                throws IOException, InterruptedException {
            
            // Write header if this is the first output
            if (isFirstOutput) {
                context.write(new Text("age,sex,cp,trestbps,chol,fbs,restecg,thalach,exang,oldpeak,slope,ca,thal,target,cluster"), 
                             new Text(""));
                isFirstOutput = false;
            }
            
            List<Point> points = new ArrayList<>();
            for (Text value : values) {
                points.add(new Point(value.toString().split(","), numDimensions));
            }
            
            if (!points.isEmpty()) {
                // Output points with cluster number as last column
                for (Point point : points) {
                    String outputLine = point.toString() + "," + key.toString();
                    context.write(new Text(outputLine), new Text(""));
                }
            }
        }
    }
    
    public static void main(String[] args) throws Exception {
        Configuration conf = new Configuration();
        
        conf.setInt("dimensions", 14);
        
        // Updated centroids with proper formatting
        conf.set("centroids", "63,1,3,145,233,1,0,150,0,2.3,0,0,1;" +
                            "67,1,4,160,286,0,0,108,1,1.5,1,3,2;" +
                            "67,1,3,120,229,0,0,129,1,2.6,1,2,3");
        
        Job job = Job.getInstance(conf, "kmeans clustering");
        job.setJarByClass(KMeansClusterer.class);
        
        job.setMapperClass(KMeansMapper.class);
        job.setReducerClass(KMeansReducer.class);
        
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);
        
        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));
        
        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}