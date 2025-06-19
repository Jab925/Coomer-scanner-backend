from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import base64
import requests
from insightface.app import FaceAnalysis

app = Flask(__name__)
CORS(app)

# Initialize model
face_app = FaceAnalysis(
    name="buffalo_l",
    root="/app/buffalo_l",
    providers=["CPUExecutionProvider"],
    download=False
)
face_app.prepare(ctx_id=0)

def decode_base64_img(b64_data):
    try:
        img_data = base64.b64decode(b64_data)
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"❌ Failed to decode image: {e}")
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
        return jsonify({'error': f'Invalid JSON: {str(e)}'}), 415

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
        return jsonify({"matches": []})

    matches = []
    for thumb in thumbnails:
        try:
            resp = requests.get(thumb["thumbnail"], timeout=5)
            if resp.status_code != 200:
                continue
            img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"❌ Error fetching thumbnail: {e}")
            continue

        if img is None:
            continue

        emb = extract_embedding(img)
        if emb is None:
            continue

        sims = [cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings]
        similarity = max(sims)

        matches.append({
            "thumbnail": thumb["thumbnail"],
            "post_url": thumb["post_url"],
            "similarity": round(similarity, 4)
        })

    return jsonify({"matches": matches})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
