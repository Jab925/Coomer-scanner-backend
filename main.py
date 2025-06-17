from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import zipfile
import numpy as np
from insightface.app import FaceAnalysis
import cv2
import base64
import requests

app = Flask(__name__)
CORS(app, origins=["https://coomer.su"])

MODEL_DIR = "/app/buffalo_l"
ZIP_PATH = "/app/buffalo_l.zip"
GDRIVE_FILE_ID = "1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo"
face_app = None

def ensure_model():
    if not os.path.exists(MODEL_DIR):
        print("📦 Model not found — downloading from Google Drive...")
        subprocess.run(["pip", "install", "--no-cache-dir", "gdown"], check=True)
        subprocess.run(["gdown", "--id", GDRIVE_FILE_ID, "-O", ZIP_PATH], check=True)
        print("✅ Download complete — extracting...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(MODEL_DIR)
        print("✅ Extraction done")
    else:
        print("✅ Model already present")

def init_face_app():
    global face_app
    ensure_model()
    face_app = FaceAnalysis(name="buffalo_l", root=MODEL_DIR)
    face_app.prepare(ctx_id=0)

def decode_base64_img(b64_data):
    img_data = base64.b64decode(b64_data)
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

def extract_embedding(img):
    faces = face_app.get(img)
    if faces:
        return faces[0].normed_embedding
    return None

def cosine_similarity(a, b):
    return float(np.dot(a, b))

@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "https://coomer.su"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({'error': f'Invalid JSON: {str(e)}'}), 415

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
        return jsonify({"matches": []})

    matches = []
    for thumb in thumbnails:
        img_url = thumb.get("thumbnail")
        resp = requests.get(img_url, timeout=5)
        img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue
        emb = extract_embedding(img)
        if emb is None:
            continue

        sims = [cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings]
        similarity = max(sims)
        matches.append({
            "thumbnail": img_url,
            "post_url": thumb.get("post_url"),
            "similarity": round(similarity, 4)
        })
        print(f"📌 Match: {img_url} → {round(similarity, 4)}")

    return jsonify({"matches": matches})

if __name__ == '__main__':
    init_face_app()
    app.run(host="0.0.0.0", port=8080)
