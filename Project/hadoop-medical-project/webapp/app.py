from flask import Flask, render_template
import pandas as pd
import json
import os

app = Flask(__name__)

def parse_kmeans_output():
    file_path = 'kmeans_results.csv'
    print(f"Reading file from: {file_path}")
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Clean column names
        df.columns = df.columns.str.strip().str.replace('\t', '')
        
        # Print debug information
        print("\nDataFrame head:")
        print(df.head())
        print("\nColumns:", df.columns.tolist())
        
        # Initialize clusters dictionary
        clusters = {}
        
        # Define feature names for better labels
        feature_names = {
            'age': 'Age (years)',
            'sex': 'Sex (0=F, 1=M)',
            'cp': 'Chest Pain Type',
            'trestbps': 'Blood Pressure (mm Hg)',
            'chol': 'Cholesterol (mg/dl)',
            'fbs': 'Fasting Blood Sugar',
            'restecg': 'Rest ECG',
            'thalach': 'Max Heart Rate',
            'exang': 'Exercise Angina',
            'oldpeak': 'ST Depression',
            'slope': 'ST Slope',
            'ca': 'Number of Vessels',
            'thal': 'Thalassemia',
            'target': 'Disease Target'
        }
        
        # Ensure cluster is numeric
        df['cluster'] = pd.to_numeric(df['cluster'])
        
        # Print unique clusters
        print("\nUnique clusters:", df['cluster'].unique())
        
        # Group by cluster and process each group
        for cluster_id, group in df.groupby('cluster'):
            # Convert numeric columns to list of points (excluding the cluster column)
            numeric_cols = list(feature_names.keys())
            points = group[numeric_cols].values.tolist()
            
            # Calculate centroid and statistics for this cluster
            centroid = group[numeric_cols].mean().tolist()
            stats = {
                'mean': group[numeric_cols].mean().to_dict(),
                'std': group[numeric_cols].std().to_dict(),
                'min': group[numeric_cols].min().to_dict(),
                'max': group[numeric_cols].max().to_dict()
            }
            
            # Store in clusters dictionary
            clusters[str(cluster_id)] = {
                'points': points,
                'centroid': centroid,
                'stats': stats,
                'size': len(points)
            }
        
        print("\nClusters dict keys:", clusters.keys())
        print("\nFirst cluster data sample:", json.dumps(clusters[next(iter(clusters))], indent=2))
        
        if not clusters:
            raise ValueError("No valid data was parsed from the file")
            
        return clusters, feature_names
        
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        raise

@app.route('/')
def dashboard():
    try:
        clusters, feature_names = parse_kmeans_output()
        
        # Calculate statistics
        stats = {
            'total_clusters': len(clusters),
            'points_per_cluster': {k: clusters[k]['size'] for k in clusters},
            'total_points': sum(clusters[k]['size'] for k in clusters),
            'features': feature_names
        }
        
        # Calculate cluster statistics
        cluster_stats = {}
        for cluster_id, cluster_data in clusters.items():
            cluster_stats[cluster_id] = cluster_data['stats']
        
        # Print debug information before rendering
        print("\nStats:", json.dumps(stats, indent=2))
        print("\nCluster Stats:", json.dumps(cluster_stats, indent=2))
        
        return render_template('dashboard.html',
                             cluster_data=json.dumps(clusters),
                             stats=json.dumps(stats),
                             cluster_stats=json.dumps(cluster_stats),
                             feature_names=json.dumps(feature_names))
                             
    except Exception as e:
        current_dir = os.getcwd()
        files_in_dir = os.listdir('.')
        
        file_preview = ""
        try:
            df = pd.read_csv('kmeans_results.csv')
            df.columns = df.columns.str.strip().str.replace('\t', '')
            file_preview = "DataFrame preview:<br>"
            file_preview += df.head().to_html()
            file_preview += f"<br>Cleaned Columns: {list(df.columns)}"
            file_preview += f"<br>Data Types: {df.dtypes.to_dict()}"
        except Exception as file_error:
            file_preview = f"Could not read file: {str(file_error)}"
        
        return f"""Error loading data: {str(e)}
                  <br>Current directory: {current_dir}
                  <br>Files in current directory: {files_in_dir}
                  <br><br>{file_preview}"""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)