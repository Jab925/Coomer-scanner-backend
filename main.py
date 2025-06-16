from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import zipfile

MODEL_URL = "https://drive.google.com/uc?export=download&id=1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo"
ZIP_PATH = "/app/buffalo_l.zip"
MODEL_DIR = "/app/buffalo_l"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def ensure_model():
    if not os.path.exists(MODEL_DIR):
        print("buffalo_l not found — downloading...")
        with requests.get(MODEL_URL, stream=True) as r:
            r.raise_for_status()
            with open(ZIP_PATH, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("✅ Download complete — checking file...")

        if not zipfile.is_zipfile(ZIP_PATH):
            raise RuntimeError("Downloaded file is not a valid zip archive")

        print("✅ Extracting...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(MODEL_DIR)
        print("✅ Extraction complete")
    else:
        print("✅ Model already present")

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    print("✅ Received /search request")
    print(f"→ Reference images: {len(data.get('references', []))}")
    print(f"→ Thumbnails: {len(data.get('thumbnails', []))}")

    thumbnails = data.get("thumbnails", [])
    return jsonify({
        "matches": [
            {
                "thumbnail": t,
                "post_url": "https://coomer.su/post/example",
                "similarity": 0.92
            } for t in thumbnails[:1]
        ]
    })

if __name__ == '__main__':
    ensure_model()
    app.run(host="0.0.0.0", port=8080)
