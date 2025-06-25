from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
import base64
import requests
from insightface.app import FaceAnalysis
import threading
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

face_app = None
app_ready = False

# === Keep-alive settings ===
KEEP_ALIVE_INTERVAL = 14 * 60  # 14 minutes
APP_URL = "https://coomer-scanner-backend-production.up.railway.app"  # Replace with your Railway URL

def keep_alive():
    while True:
        try:
            print("⏳ Keep-alive ping...")
            res = requests.get(f"{APP_URL}/health", timeout=10)
            if res.status_code != 200:
                print("⚠️ Health check failed, triggering /wake")
                requests.get(f"{APP_URL}/wake")
        except Exception as e:
            print(f"❌ Keep-alive error: {e}")
        time.sleep(KEEP_ALIVE_INTERVAL)

# === Lazy load face model ===
def get_face_app():
    global face_app, app_ready
    if face_app is None:
        try:
            print("⚙️ Initializing FaceAnalysis...")
            face_app = FaceAnalysis(
                name="buffalo_l",
                root="/app/buffalo_l",
                providers=["CPUExecutionProvider"],
                download=False
            )
            face_app.prepare(ctx_id=0)
            print("✅ FaceAnalysis loaded.")
            app_ready = True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            app_ready = False
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
    fa = get_face_app()
    if not fa:
        return None
    faces = fa.get(img)
    if faces:
        return faces[0].normed_embedding
    return None

def cosine_similarity(a, b):
    return float(np.dot(a, b))

@app.route("/")
def index():
    return "Backend running."

@app.route("/health")
def health():
    return jsonify({"status": "ok", "ready": app_ready})

@app.route("/wake")
def wake():
    threading.Thread(target=get_face_app).start()
    return jsonify({"status": "warming up"})

@app.route("/search", methods=["POST"])
def search():
    global app_ready
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"❌ Invalid JSON: {e}")
        return jsonify({'error': 'Invalid JSON'}), 415

    if not app_ready:
        print("🚫 Model not ready yet.")
        return jsonify({'error': 'Model not ready. Call /wake first.'}), 503

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
        print("⚠ No valid reference embeddings.")
        return jsonify({"matches": []})

    matches = []
    for thumb in thumbnails:
        try:
            resp = requests.get(thumb["thumbnail"], timeout=5)
            if resp.status_code != 200:
                continue
            img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"❌ Error loading thumbnail: {e}")
            continue

        if img is None:
            continue

        emb = extract_embedding(img)
        if emb is None:
            continue

        sims = [cosine_similarity(emb, ref_emb) for ref_emb in ref_embeddings]
        similarity = max(sims)
        normalized = (similarity + 1) / 2  # Convert cosine [-1,1] to [0,1]

        print(f"🔍 Match: {thumb['thumbnail']} → raw {similarity:.4f}, norm {normalized:.4f}")

        matches.append({
            "thumbnail": thumb["thumbnail"],
            "post_url": thumb["post_url"],
            "similarity": round(normalized, 4)
        })

    return jsonify({"matches": matches})


# === Start keep-alive in background ===
threading.Thread(target=keep_alive, daemon=True).start()
