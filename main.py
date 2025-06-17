from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import base64
import requests
from insightface.app import FaceAnalysis

app = Flask(__name__)
CORS(app, origins=["https://coomer.su"])

face_app = None
MODEL_DIR = "/app/buffalo_l"  # Path inside your Docker where buffalo_l is pre-bundled

def init_face_app():
    global face_app
    face_app = FaceAnalysis(name="buffalo_l", root=MODEL_DIR, providers=["CPUExecutionProvider"])
    face_app.prepare(ctx_id=0)
    print("✅ FaceAnalysis model loaded")

def decode_base64_img(data):
    try:
        img_bytes = base64.b64decode(data)
        img_np = np.frombuffer(img_bytes, np.uint8)
        return cv2.imdecode(img_np, cv2.IMREAD_COLOR)
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
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({'error': f'Invalid JSON: {str(e)}'}), 400

    print("✅ Received /search request")
    references = data.get("references", [])
    thumbnails = data.get("thumbnails", [])

    ref_embeddings = []
    for ref in references:
        img = decode_base64_img(ref.get("data", ""))
        if img is not None:
            emb = extract_embedding(img)
            if emb is not None:
                ref_embeddings.append(emb)

    if not ref_embeddings:
        print("⚠ No valid reference embeddings")
        return jsonify({"matches": []})

    matches = []
    for thumb in thumbnails:
        img_url = thumb.get("thumbnail")
        post_url = thumb.get("post_url")
        try:
            resp = requests.get(img_url, timeout=5)
            img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"❌ Failed to load image {img_url}: {e}")
            continue

        if img is None:
            continue

        emb = extract_embedding(img)
        if emb is None:
            continue

        sims = [cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings]
        max_sim = max(sims)
        matches.append({
            "thumbnail": img_url,
            "post_url": post_url,
            "similarity": round(max_sim, 4)
        })
        print(f"📌 {img_url} → {round(max_sim, 4)}")

    return jsonify({"matches": matches})

if __name__ == '__main__':
    init_face_app()
    app.run(host="0.0.0.0", port=8080)
