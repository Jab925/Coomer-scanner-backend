from flask import Flask, request, jsonify, render_template
from search_coomer import find_matches
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return "OK"

@app.route("/keep-alive")
def keep_alive():
    return "still alive"

@app.route("/client-scan", methods=["POST"])
def client_scan():
    files = request.files.getlist("images")
    thumb_data = request.form.get("thumb_data")
    match_type = request.form.get("type", "both")
    threshold = float(request.form.get("threshold", 0.3))
    if not files or not thumb_data:
        return jsonify({"error": "Missing required data"}), 400
    results = find_matches(files, thumb_data, match_type, threshold)
    return jsonify({"matches": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
