from flask import Flask, render_template
import pandas as pd
import json

app = Flask(__name__)

def parse_kmeans_output():
    df = pd.read_csv('kmeans_results.csv')
    df.columns = df.columns.str.strip().str.replace('\t', '')
    
    clusters = {}
    
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
    
    df['cluster'] = pd.to_numeric(df['cluster'])
    
    for cluster_id, group in df.groupby('cluster'):
        numeric_cols = list(feature_names.keys())
        points = group[numeric_cols].values.tolist()
        
        centroid = group[numeric_cols].mean().tolist()
        stats = {
            'mean': group[numeric_cols].mean().to_dict(),
            'std': group[numeric_cols].std().to_dict(),
            'min': group[numeric_cols].min().to_dict(),
            'max': group[numeric_cols].max().to_dict()
        }
        
        clusters[str(cluster_id)] = {
            'points': points,
            'centroid': centroid,
            'stats': stats,
            'size': len(points)
        }
            
    return clusters, feature_names

@app.route('/')
def dashboard():
    clusters, feature_names = parse_kmeans_output()
    
    stats = {
        'total_clusters': len(clusters),
        'points_per_cluster': {k: clusters[k]['size'] for k in clusters},
        'total_points': sum(clusters[k]['size'] for k in clusters),
        'features': feature_names
    }
    
    cluster_stats = {
        cluster_id: cluster_data['stats'] 
        for cluster_id, cluster_data in clusters.items()
    }
    
    return render_template('dashboard.html',
                         cluster_data=json.dumps(clusters),
                         stats=json.dumps(stats),
                         cluster_stats=json.dumps(cluster_stats),
                         feature_names=json.dumps(feature_names))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)