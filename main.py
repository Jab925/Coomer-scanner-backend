from flask import Flask, request, jsonify
from flask_cors import CORS
from search_coomer import find_matches
import base64
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

LOG_PATH = "logs.txt"

def log(msg):
    print(msg)
    with open(LOG_PATH, "a") as f:
        f.write(msg + "\n")

@app.route("/health")
def health():
    return "ok"

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    references = data.get("references", [])
    thumbnails = data.get("thumbnails", [])

    log(f"[POST] /search called")
    log(f"→ Received {len(references)} reference image(s)")
    log(f"→ Received {len(thumbnails)} thumbnails")

    try:
        matches = find_matches(references, thumbnails, threshold=0.35)
        log(f"→ Found {len(matches)} matches ≥ 35%")
        return jsonify({ "matches": matches }), 200
    except Exception as e:
        log(f"[ERROR] {str(e)}")
        return jsonify({ "error": str(e) }), 500

if __name__ == "__main__":
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, "w"): pass
    app.run(host="0.0.0.0", port=8080)
