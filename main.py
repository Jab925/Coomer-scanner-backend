from flask import Flask, request, jsonify
from flask_cors import CORS
import base64

app = Flask(__name__)
CORS(app)  # enable CORS for all domains

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/client-scan", methods=["POST"])
def scan():
    try:
        data = request.get_json()
        print("✅ Received scan request")
        print("→ Reference images:", len(data.get("references", [])))
        print("→ Thumbnails:", len(data.get("thumbnails", [])))

        # TEMP SIMULATED MATCH RESPONSE
        thumbnails = data.get("thumbnails", [])
        return jsonify({
            "matches": [
                {
                    "thumbnail": t,
                    "post_url": "https://coomer.su/post/example",
                    "similarity": 0.92
                }
                for t in thumbnails[:1]
            ]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
