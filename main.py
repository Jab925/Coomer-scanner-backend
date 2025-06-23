from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import base64
import requests
from insightface.app import FaceAnalysis

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Lazy-load FaceAnalysis so Railway doesn't kill the app on slow startup
face_app = None

def get_face_app():
    global face_app
    if face_app is None:
        face_app = FaceAnalysis(
            name="buffalo_l",
            root="/app/buffalo_l",
            providers=["CPUExecutionProvider"],
            download=False
        )
        face_app.prepare(ctx_id=0)
    return face_app

def decode_base64_img(b64_data):
    try:
        img_data = base64.b64decode(b64_data)
        np_arr = np.frombuffer(img_data, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"❌ Failed to decode image: {e}")
        return None

def extract_embedding(img):
    face_app = get_face_app()
    faces = face_app.get(img)
    if faces:
        return faces[0].normed_embedding
    return None

def cosine_similarity(a, b):
    return float(np.dot(a, b))

@app.route('/')
def index():
    return "OK"

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    print("🚀 /search request received")

    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"❌ Invalid JSON: {e}")
        return jsonify({'error': 'Invalid JSON'}), 415

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

    # TEMP LIMIT for testing
    thumbnails = thumbnails[:5]

    matches = []
    for thumb in thumbnails:
        try:
            print(f"🌐 Fetching thumbnail: {thumb['thumbnail']}")
            resp = requests.get(thumb["thumbnail"], timeout=1)
            if resp.status_code != 200:
                print(f"❌ Failed to load {thumb['thumbnail']} — status {resp.status_code}")
                continue
            img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"⚠ Failed to load thumbnail {thumb['thumbnail']} : {e}")
            continue

        if img is None:
            print(f"❌ Decoding failed for {thumb['thumbnail']}")
            continue

        emb = extract_embedding(img)
        if emb is None:
            print(f"⚠ No face found in {thumb['thumbnail']}")
            continue

        sims = [cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings]
        similarity = max(sims)
        normalized = (similarity + 1) / 2
        print(f"✅ Match: {thumb['thumbnail']} → raw {similarity:.4f}, normalized {normalized:.4f}")

        matches.append({
            "thumbnail": thumb["thumbnail"],
            "post_url": thumb["post_url"],
            "similarity": round(normalized, 4)
        })

    print(f"🎯 /search finished. {len(matches)} matches found")
    return jsonify({"matches": matches})
