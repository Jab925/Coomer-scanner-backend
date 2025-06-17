from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from insightface.app import FaceAnalysis
import base64
import requests

app = Flask(__name__)
CORS(app)

# Initialize face analysis app with model loaded from docker-bundled directory
face_app = FaceAnalysis(name="buffalo_l", root="/app/buffalo_l")
face_app.prepare(ctx_id=0)

def decode_base64_img(b64_data):
    try:
        img_data = base64.b64decode(b64_data)
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"❌ Failed to decode base64 image: {e}")
        return None

def extract_embedding(img):
    faces = face_app.get(img)
    if faces:
        return faces[0].normed_embedding
    return None

def cosine_similarity(a, b):
    return float(np.dot(a, b))

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json(force=True)
    print("✅ Received /search request")

    references_data = data.get("references", [])
    thumbnails_data = data.get("thumbnails", [])

    print(f"→ Reference images: {len(references_data)}")
    print(f"→ Thumbnails: {len(thumbnails_data)}")

    ref_embeddings = []
    for ref in references_data:
        img = decode_base64_img(ref.get("data", ""))
        if img is not None:
            emb = extract_embedding(img)
            if emb is not None:
                ref_embeddings.append(emb)

    if not ref_embeddings:
        return jsonify({"matches": []})

    matches = []
    for thumb in thumbnails_data:
        img_url = thumb.get("thumbnail")
        try:
            response = requests.get(img_url, timeout=10)
            img_arr = np.frombuffer(response.content, np.uint8)
            img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"❌ Failed to load thumbnail {img_url}: {e}")
            continue

        if img is None:
            continue

        emb = extract_embedding(img)
        if emb is None:
            continue

        similarity = max(cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings)

        matches.append({
            "thumbnail": img_url,
            "post_url": thumb.get("post_url"),
            "similarity": round(similarity, 4)
        })

    return jsonify({"matches": matches})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
