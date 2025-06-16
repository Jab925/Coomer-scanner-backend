from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import zipfile
import base64
import numpy as np
import cv2
from insightface.app import FaceAnalysis

app = Flask(__name__)
CORS(app)

MODEL_DIR = "/app/buffalo_l"
ZIP_PATH = "/app/buffalo_l.zip"
GDRIVE_FILE_ID = "1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo"

def ensure_model():
    if not os.path.exists(MODEL_DIR):
        print("📦 Model not found — downloading...")
        subprocess.run(["pip", "install", "--no-cache-dir", "gdown"], check=True)
        subprocess.run(["gdown", "--id", GDRIVE_FILE_ID, "-O", ZIP_PATH], check=True)
        print("✅ Downloaded. Extracting...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall("/app/")
        print("✅ Extracted.")
    else:
        print("✅ Model already present.")

# Ensure model is downloaded
ensure_model()

# Load model
face_app = FaceAnalysis(name='buffalo_l', root=MODEL_DIR)
face_app.prepare(ctx_id=0)

def decode_b64_image(b64str):
    data = base64.b64decode(b64str)
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

def get_embedding(b64str):
    img = decode_b64_image(b64str)
    faces = face_app.get(img)
    if faces:
        return faces[0].embedding
    return None

def cosine_sim(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json(force=True)
    refs = data.get("references", [])
    thumbs = data.get("thumbnails", [])

    ref_embeds = []
    for ref in refs:
        embed = get_embedding(ref["data"])
        if embed is not None:
            ref_embeds.append(embed)

    matches = []
    for thumb in thumbs:
        embed = get_embedding(thumb["data"])
        if embed is None:
            continue
        sims = [cosine_sim(embed, r) for r in ref_embeds]
        best = max(sims) if sims else 0
        matches.append({
            "thumbnail": thumb["thumbnail"],
            "post_url": thumb["post_url"],
            "similarity": best
        })
        print(f"📌 {thumb['thumbnail']} → {best:.4f}")

    return jsonify({"matches": matches})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
