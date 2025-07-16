from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import base64
import requests
import logging
import threading
import time
from insightface.app import FaceAnalysis
from PIL import Image
import imagehash
from io import BytesIO

# === Config ===
APP_URL = "https://coomer-scanner-backend-production.up.railway.app"
KEEP_ALIVE_INTERVAL = 60
TATTOO_THRESHOLD = 8  # Lower is more similar for perceptual hashes

# === App Setup ===
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

face_app = None
ref_hashes = []

def get_face_app():
    global face_app
    if face_app is None:
        try:
            logging.info("⏳ Initializing FaceAnalysis model...")
            face_app = FaceAnalysis(
                name="buffalo_l",
                root="/app/buffalo_l",
                providers=["CPUExecutionProvider"],
                download=False
            )
            face_app.prepare(ctx_id=0)
            logging.info("✅ FaceAnalysis model ready")
        except Exception as e:
            logging.error(f"❌ Failed to initialize FaceAnalysis: {e}")
            raise
    return face_app

def decode_base64_img(b64_data):
    try:
        img_data = base64.b64decode(b64_data)
        np_arr = np.frombuffer(img_data, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        logging.error(f"❌ Failed to decode base64 image: {e}")
        return None

def extract_embedding(img):
    try:
        face_app = get_face_app()
        faces = face_app.get(img)
        if faces:
            return faces[0].normed_embedding
    except Exception as e:
        logging.error(f"❌ Embedding extraction failed: {e}")
    return None

def compute_hash(img):
    try:
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        return imagehash.phash(pil_img)
    except Exception as e:
        logging.error(f"❌ Hash computation failed: {e}")
        return None

def cosine_similarity(a, b):
    return float(np.dot(a, b))

@app.route("/")
def index():
    return "Backend is running"

@app.route("/health")
def health():
    return "ok"

@app.route("/search", methods=["POST"])
def search():
    global ref_hashes
    try:
        data = request.get_json(force=True)
    except Exception as e:
        logging.error(f"❌ Invalid JSON input: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    references = data.get("references", [])
    thumbnails = data.get("thumbnails", [])

    ref_embeddings = []
    ref_hashes = []

    for ref in references:
        img = decode_base64_img(ref.get("data", ""))
        if img is not None:
            emb = extract_embedding(img)
            if emb is not None:
                ref_embeddings.append(emb)
            else:
                ref_hash = compute_hash(img)
                if ref_hash:
                    ref_hashes.append(ref_hash)

    if not ref_embeddings and not ref_hashes:
        logging.warning("⚠️ No usable reference data")
        return jsonify({"matches": []})

    matches = []

    for thumb in thumbnails:
        try:
            resp = requests.get(thumb["thumbnail"], timeout=3)
            if resp.status_code != 200:
                continue
            img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                continue
        except Exception as e:
            logging.warning(f"❌ Failed to fetch thumbnail {thumb['thumbnail']}: {e}")
            continue

        emb = extract_embedding(img)
        if emb is not None and ref_embeddings:
            sims = [cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings]
            similarity = max(sims)
            normalized = (similarity + 1) / 2
            matches.append({
                "thumbnail": thumb["thumbnail"],
                "post_url": thumb["post_url"],
                "similarity": round(normalized, 4)
            })
            logging.info(f"✅ Face Match: {thumb['thumbnail']} → {normalized:.4f}")
        elif ref_hashes:
            thumb_hash = compute_hash(img)
            if thumb_hash:
                distances = [thumb_hash - h for h in ref_hashes]
                best = min(distances)
                if best <= TATTOO_THRESHOLD:
                    similarity = 1 - (best / 64)
                    matches.append({
                        "thumbnail": thumb["thumbnail"],
                        "post_url": thumb["post_url"],
                        "similarity": round(similarity, 4)
                    })
                    logging.info(f"🎯 Tattoo Match: {thumb['thumbnail']} → dist={best}, sim={similarity:.4f}")

    return jsonify({"matches": matches})


# === Keep Alive Thread ===
def keep_alive():
    time.sleep(30)
    while True:
        try:
            logging.debug("🔁 Keep-alive ping...")
            res = requests.get(f"{APP_URL}/health", timeout=10)
            if res.status_code == 200:
                logging.debug("✅ Keep-alive OK")
            else:
                logging.warning(f"⚠️ Keep-alive response: {res.status_code}")
        except Exception as e:
            logging.warning(f"❌ Keep-alive error: {e}")
        time.sleep(KEEP_ALIVE_INTERVAL)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    threading.Thread(target=keep_alive, daemon=True).start()
    logging.info("🚀 Launching Flask backend")
    app.run(host="0.0.0.0", port=8080)
