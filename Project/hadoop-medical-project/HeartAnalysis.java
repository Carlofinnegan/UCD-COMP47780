// HeartAnalysis.java
package com.heartanalysis;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.io.LongWritable;

import java.io.IOException;

public class HeartAnalysis {
    public static class HeartMapper extends Mapper<LongWritable, Text, Text, Text> {
        private Text ageGroup = new Text();
        private Text values = new Text();

        private String getAgeGroup(int age) {
            if (age < 40) return "30-39";
            else if (age < 50) return "40-49";
            else if (age < 60) return "50-59";
            else return "60+";
        }

        @Override
        public void map(LongWritable key, Text value, Context context) throws IOException, InterruptedException {
            if (key.get() == 0) return; // Skip header

            String[] fields = value.toString().split(",");
            try {
                int age = Integer.parseInt(fields[0]);
                double cholesterol = Double.parseDouble(fields[3]);
                double heartRate = Double.parseDouble(fields[7]);
                double bloodPressure = Double.parseDouble(fields[4]);

                ageGroup.set(getAgeGroup(age));
                // Format: cholesterol,heartRate,bloodPressure,count
                values.set(String.format("%.1f,%.1f,%.1f,1", cholesterol, heartRate, bloodPressure));
                context.write(ageGroup, values);
            } catch (Exception e) {
                // Skip malformed records
            }
        }
    }

    public static class HeartReducer extends Reducer<Text, Text, Text, Text> {
        private Text result = new Text();

        @Override
        public void reduce(Text key, Iterable<Text> values, Context context) throws IOException, InterruptedException {
            double cholesterolSum = 0;
            double heartRateSum = 0;
            double bloodPressureSum = 0;
            int count = 0;

            for (Text val : values) {
                String[] fields = val.toString().split(",");
                cholesterolSum += Double.parseDouble(fields[0]);
                heartRateSum += Double.parseDouble(fields[1]);
                bloodPressureSum += Double.parseDouble(fields[2]);
                count += Integer.parseInt(fields[3]);
            }

            String stats = String.format("Avg Cholesterol: %.1f, Avg Heart Rate: %.1f, Avg Blood Pressure: %.1f, Count: %d",
                    cholesterolSum/count, heartRateSum/count, bloodPressureSum/count, count);
            result.set(stats);
            context.write(key, result);
        }
    }

    public static void main(String[] args) throws Exception {
        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "heart analysis");
        
        job.setJarByClass(HeartAnalysis.class);
        job.setMapperClass(HeartMapper.class);
        job.setReducerClass(HeartReducer.class);
        
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);
        
        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));
        
        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}