from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import base64

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route("/api/health")
def health():
    return jsonify({
        "message": "Coomer Face/Tattoo Scanner Backend is running",
        "model_ready": True,
        "model_status": "loaded",
        "port": 8080,
        "status": "ok"
    })

@app.route("/client-scan", methods=["POST"])
def scan_thumbnails():
    try:
        data = request.get_json()
        refs = data.get("refs", [])
        thumbnails = data.get("thumbnails", [])

        if not refs or not thumbnails:
            return jsonify({"error": "Missing reference or thumbnail data"}), 400

        # Simulated response — replace with actual InsightFace matching logic
        dummy_results = []

        for thumb_url in thumbnails:
            dummy_results.append({
                "similarity": round(np.random.uniform(0.6, 0.9), 2),
                "thumbnail": thumb_url,
                "match_type": "face",
                "post_url": thumb_url.replace("thumbnail", "post")
            })

        return jsonify({"matches": dummy_results}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
