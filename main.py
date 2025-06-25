from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import requests
import time
import logging
import numpy as np
import cv2
import base64
from insightface.app import FaceAnalysis

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

face_app = None
KEEP_ALIVE_INTERVAL = 60  # seconds
APP_URL = "https://coomer-scanner-backend-production.up.railway.app"  # change if needed

def get_face_app():
    global face_app
    if face_app is None:
        logging.info("🧠 Loading FaceAnalysis model...")
        face_app = FaceAnalysis(
            name="buffalo_l",
            root="/app/buffalo_l",
            providers=["CPUExecutionProvider"],
            download=False
        )
        face_app.prepare(ctx_id=0)
        logging.info("✅ FaceAnalysis model loaded.")
    return face_app

def decode_base64_img(b64_data):
    try:
        img_data = base64.b64decode(b64_data)
        np_arr = np.frombuffer(img_data, np.uint8)
        return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    except Exception as e:
        logging.warning(f"❌ Failed to decode image: {e}")
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
    logging.info("📬 / called")
    return "OK"

@app.route('/health')
def health():
    logging.info("✅ /health check passed")
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    logging.info("🔍 /search request received")
    try:
        data = request.get_json(force=True)
    except Exception as e:
        logging.error(f"❌ Invalid JSON: {e}")
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
        logging.warning("⚠ No valid reference embeddings")
        return jsonify({"matches": []})

    matches = []
    for thumb in thumbnails:
        try:
            resp = requests.get(thumb["thumbnail"], timeout=3)
            if resp.status_code != 200:
                continue
            img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
        except:
            continue

        if img is None:
            continue

        emb = extract_embedding(img)
        if emb is None:
            continue

        sims = [cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings]
        similarity = max(sims)
        normalized = (similarity + 1) / 2
        logging.info(f"✅ Match: {thumb['thumbnail']} → raw {similarity:.4f}, normalized {normalized:.4f}")

        matches.append({
            "thumbnail": thumb["thumbnail"],
            "post_url": thumb["post_url"],
            "similarity": round(normalized, 4)
        })

    return jsonify({"matches": matches})

def keep_alive():
    while True:
        try:
            logging.debug("⏳ Keep-alive ping...")
            res = requests.get(f"{APP_URL}/health", timeout=10)
            logging.debug(f"🔁 Keep-alive response: {res.status_code}")
        except Exception as e:
            logging.warning(f"❌ Keep-alive error: {e}")
        time.sleep(KEEP_ALIVE_INTERVAL)

# ✅ Important: Start keep-alive only in actual Python run
if __name__ != "gunicorn":
    threading.Thread(target=keep_alive, daemon=True).start()
