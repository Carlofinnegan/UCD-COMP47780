from flask import Flask, render_template, jsonify
from hdfs import InsecureClient
import pandas as pd
import logging
import os
import json
from collections import defaultdict

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

HDFS_NAMENODE_URL = os.getenv('HDFS_NAMENODE_URL', 'http://namenode:9870')

# Updated column mappings based on your CSV
COLUMN_MAPPINGS = {
    'age': 'age',
    'cholesterol': 'chol',
    'heart_rate': 'thalach',  # maximum heart rate achieved
    'blood_pressure': 'trestbps',  # resting blood pressure
    'chest_pain': 'cp'  # chest pain type
}

def run_mapreduce():
    """MapReduce operation on heart data with correct column names"""
    try:
        # Read data from HDFS
        client = InsecureClient(HDFS_NAMENODE_URL)
        with client.read('/user/root/heart.csv') as reader:
            df = pd.read_csv(reader)
            logger.info(f"Read {len(df)} records from HDFS")

        # Map phase: Group by age and collect values
        mapped_data = defaultdict(list)
        for _, row in df.iterrows():
            age_group = (row[COLUMN_MAPPINGS['age']] // 10) * 10
            mapped_data[age_group].append({
                'cholesterol': float(row[COLUMN_MAPPINGS['cholesterol']]),
                'heart_rate': float(row[COLUMN_MAPPINGS['heart_rate']]),
                'blood_pressure': float(row[COLUMN_MAPPINGS['blood_pressure']]),
                'chest_pain': int(row[COLUMN_MAPPINGS['chest_pain']])
            })

        # Reduce phase: Calculate statistics for each age group
        reduced_data = {}
        for age_group, values in mapped_data.items():
            reduced_data[age_group] = {
                'avg_cholesterol': round(sum(v['cholesterol'] for v in values) / len(values), 2),
                'avg_heart_rate': round(sum(v['heart_rate'] for v in values) / len(values), 2),
                'avg_blood_pressure': round(sum(v['blood_pressure'] for v in values) / len(values), 2),
                'chest_pain_distribution': {
                    i: sum(1 for v in values if v['chest_pain'] == i) for i in range(4)
                },
                'count': len(values)
            }

        logger.info(f"Analysis completed for {len(reduced_data)} age groups")
        return reduced_data
    except Exception as e:
        logger.error(f"MapReduce error: {str(e)}", exc_info=True)
        return None

@app.route('/')
def index():
    try:
        # Run MapReduce analysis
        analysis_results = run_mapreduce()
        
        if not analysis_results:
            return render_template('error.html', 
                                error="Failed to analyze data. Check logs for details.")

        # Prepare data for plotting
        age_groups = sorted(analysis_results.keys())
        plots = {
            'cholesterol': {
                'x': [f"{ag}s" for ag in age_groups],
                'y': [analysis_results[ag]['avg_cholesterol'] for ag in age_groups],
                'type': 'bar',
                'name': 'Avg Cholesterol'
            },
            'heart_rate': {
                'x': [f"{ag}s" for ag in age_groups],
                'y': [analysis_results[ag]['avg_heart_rate'] for ag in age_groups],
                'type': 'bar',
                'name': 'Avg Heart Rate'
            },
            'blood_pressure': {
                'x': [f"{ag}s" for ag in age_groups],
                'y': [analysis_results[ag]['avg_blood_pressure'] for ag in age_groups],
                'type': 'bar',
                'name': 'Avg Blood Pressure'
            },
            'distribution': {
                'x': [f"{ag}s" for ag in age_groups],
                'y': [analysis_results[ag]['count'] for ag in age_groups],
                'type': 'bar',
                'name': 'Number of Patients'
            }
        }

        return render_template('dashboard.html',
                             plots=json.dumps(plots),
                             analysis_results=analysis_results)

    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

@app.route('/debug')
def debug_info():
    """Endpoint for debugging"""
    try:
        client = InsecureClient(HDFS_NAMENODE_URL)
        df = pd.read_csv('/app/heart.csv')
        
        return jsonify({
            'columns': df.columns.tolist(),
            'sample_data': df.head().to_dict(),
            'column_mappings': COLUMN_MAPPINGS,
            'hdfs_status': client.status('/user/root/heart.csv', strict=False)
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)