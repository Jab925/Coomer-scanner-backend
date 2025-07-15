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
import imagehash
from PIL import Image
import io

# === Config ===
APP_URL = "https://coomer-scanner-backend-production.up.railway.app"
KEEP_ALIVE_INTERVAL = 60
TATTOO_SIM_THRESHOLD = 0.6  # 60% match using perceptual hash

# === App Setup ===
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

face_app = None

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

def cosine_similarity(a, b):
    return float(np.dot(a, b))

def phash_image(img):
    try:
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return imagehash.phash(img_pil)
    except Exception as e:
        logging.warning(f"❌ pHash error: {e}")
        return None

@app.route("/")
def index():
    return "Backend is running"

@app.route("/health")
def health():
    return "ok"

@app.route("/search", methods=["POST"])
def search():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        logging.error(f"❌ Invalid JSON input: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    references = data.get("references", [])
    thumbnails = data.get("thumbnails", [])

    ref_embeddings = []
    ref_phashes = []
    for ref in references:
        img = decode_base64_img(ref.get("data", ""))
        if img is not None:
            emb = extract_embedding(img)
            if emb is not None:
                ref_embeddings.append(emb)
            ph = phash_image(img)
            if ph is not None:
                ref_phashes.append(ph)

    if not ref_embeddings and not ref_phashes:
        logging.warning("⚠️ No usable reference embeddings or phashes")
        return jsonify({"matches": []})

    matches = []
    for thumb in thumbnails:
        try:
            resp = requests.get(thumb["thumbnail"], timeout=5)
            if resp.status_code != 200:
                continue
            img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                continue
        except Exception as e:
            logging.warning(f"❌ Failed to fetch thumbnail {thumb['thumbnail']}: {e}")
            continue

        # Try face match
        match_type = None
        similarity = 0.0
        emb = extract_embedding(img)
        if emb and ref_embeddings:
            sims = [cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings]
            similarity = max(sims)
            similarity = round((similarity + 1) / 2, 4)  # normalize 0–1
            match_type = "face"

        # Try tattoo match if no face match or no strong result
        if (not emb or similarity < TATTOO_SIM_THRESHOLD) and ref_phashes:
            thumb_ph = phash_image(img)
            if thumb_ph:
                sims = [1 - (thumb_ph - ref_ph) / 64 for ref_ph in ref_phashes]
                best = max(sims)
                if best >= TATTOO_SIM_THRESHOLD:
                    similarity = round(best, 4)
                    match_type = "tattoo"

        if similarity >= TATTOO_SIM_THRESHOLD:
            matches.append({
                "thumbnail": thumb["thumbnail"],
                "post_url": thumb["post_url"],
                "similarity": similarity,
                "type": match_type
            })
            logging.info(f"✅ Match ({match_type}): {thumb['thumbnail']} → {similarity:.4f}")

    return jsonify({"matches": matches})

# === Keep Alive ===
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
