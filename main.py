from flask import Flask, request, jsonify
from flask_cors import CORS
import base64

app = Flask(__name__)
CORS(app)  # ← this line enables CORS for all domains

@app.route("/health")
def health():
    return "ok"

@app.route("/client-scan", methods=["POST"])
def scan():
    data = request.get_json()
    print("✅ Received scan request")
    print("→ Reference images:", len(data.get("references", [])))
    print("→ Thumbnails:", len(data.get("thumbnails", [])))

    return jsonify({
        "matches": [
            {
                "thumbnail": t,
                "post_url": "https://coomer.su/post/example",
                "similarity": 0.92
            } for t in data.get("thumbnails", [])[:1]
        ]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
