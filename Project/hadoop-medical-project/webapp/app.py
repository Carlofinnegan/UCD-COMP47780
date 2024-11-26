from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Load data from the exported file
def load_results():
    data = []
    try:
        with open("wordcount_results.txt", "r") as f:
            for line in f:
                word, count = line.strip().split("\t")
                data.append({"word": word, "count": int(count)})
    except Exception as e:
        print(f"Error loading data: {e}")
    return data

@app.route("/")
def index():
    data = load_results()
    return render_template("index.html", data=data)

@app.route("/api/data")
def api_data():
    data = load_results()
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
