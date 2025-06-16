from flask import Flask, request, jsonify
from flask_cors import CORS
from insightface.app import FaceAnalysis
import os
import requests
import zipfile

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

MODEL_URL = "https://drive.google.com/uc?export=download&id=1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo"
ZIP_PATH = "/app/buffalo_l.zip"
MODEL_DIR = "/app/buffalo_l"

def ensure_model():
    if not os.path.exists(MODEL_DIR):
        print("📦 Model not found — downloading from Google Drive...")
        with requests.get(MODEL_URL, stream=True) as r:
            r.raise_for_status()
            with open(ZIP_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("✅ Download complete — extracting...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(MODEL_DIR)
        print("✅ Extraction done")
    else:
        print("✅ Model already present")

# Download + extract model before server starts
ensure_model()

# Initialize face analysis app
face_app = FaceAnalysis(name=MODEL_DIR, providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0)

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    print(f"✅ Received /search with {len(data.get('references', []))} references and {len(data.get('thumbnails', []))} thumbnails")

    # Dummy match for testing
    thumbnails = data.get("thumbnails", [])
    matches = []
    for t in thumbnails[:1]:
        matches.append({
            "thumbnail": t,
            "post_url": "https://coomer.su/post/example",
            "similarity": 0.92
        })

    return jsonify({"matches": matches})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
