from flask import Flask, request, jsonify
from flask_cors import CORS
from insightface.app import FaceAnalysis

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize the face analysis app with the local buffalo_l model directory
face_app = FaceAnalysis(name="/app/buffalo_l", providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    references = data.get("references", [])
    thumbnails = data.get("thumbnails", [])

    print("✅ Received /search request")
    print(f"→ Reference images: {len(references)}")
    print(f"→ Thumbnails: {len(thumbnails)}")

    # In real code you'd process the embeddings here.
    # This is a dummy matcher response for now:
    matches = []
    for t in thumbnails[:1]:
        matches.append({
            "thumbnail": t,
            "post_url": "https://coomer.su/post/example",
            "similarity": 0.92
        })

    return jsonify({"matches": matches})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
