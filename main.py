from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import base64
import requests
from insightface.app import FaceAnalysis

app = Flask(__name__)
CORS(app, origins=["https://coomer.su"])  # Allow only coomer.su frontend

MODEL_DIR = "/app/buffalo_l"
face_app = None

def init_face_app():
    global face_app
    face_app = FaceAnalysis(name="buffalo_l", root=MODEL_DIR, providers=["CPUExecutionProvider"])
    face_app.prepare(ctx_id=0)
    print("✅ Face model loaded and ready")

def decode_base64_img(b64_data):
    try:
        img_data = base64.b64decode(b64_data)
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"❌ Failed to decode base64 image: {e}")
        return None

def download_and_decode_url(url):
    try:
        resp = requests.get(url, timeout=10)
        np_arr = np.frombuffer(resp.content, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"❌ Failed to fetch image {url}: {e}")
        return None

def get_embedding(img):
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
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400

    references = data.get("references", [])
    thumbnails = data.get("thumbnails", [])

    print(f"✅ Received {len(references)} references and {len(thumbnails)} thumbnails")

    # Process reference images
    ref_embeddings = []
    for ref in references:
        img = decode_base64_img(ref.get("data", ""))
        if img is not None:
            emb = get_embedding(img)
            if emb is not None:
                ref_embeddings.append(emb)

    if not ref_embeddings:
        print("❌ No valid reference embeddings")
        return jsonify({"matches": []})

    # Process thumbnails
    matches = []
    for thumb in thumbnails:
        img_url = thumb.get("thumbnail")
        post_url = thumb.get("post_url")
        img = download_and_decode_url(img_url)
        if img is None:
            continue
        emb = get_embedding(img)
        if emb is None:
            continue

        similarities = [cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings]
        max_sim = max(similarities)
        matches.append({
            "thumbnail": img_url,
            "post_url": post_url,
            "similarity": round(max_sim, 4)
        })

    return jsonify({"matches": matches})

if __name__ == '__main__':
    init_face_app()
    app.run(host="0.0.0.0", port=8080)
