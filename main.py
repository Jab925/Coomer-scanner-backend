from flask import Flask, request, jsonify
from flask_cors import CORS
from search_coomer import find_matches
import time

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/search": {"origins": "*"}})

@app.route("/health")
def health():
    return "ok"

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    references = data.get("references", [])
    thumbnails = data.get("thumbnails", [])

    print(f"[✅ /search] {len(references)} reference(s), {len(thumbnails)} thumbnails")
    start = time.time()
    try:
        matches = find_matches(references, thumbnails, threshold=0.35)
    except Exception as e:
        print(f"[❌ ERROR] Matching failed: {e}")
        return jsonify({"error": str(e)}), 500

    print(f"[✅ /search] Done in {time.time() - start:.2f}s — {len(matches)} match(es)")
    return jsonify({"matches": matches})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
