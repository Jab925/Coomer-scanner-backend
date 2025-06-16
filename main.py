from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import zipfile

app = Flask(__name__)
# Allow only coomer.su to call your API
CORS(app, origins=["https://coomer.su"])

MODEL_DIR = "/app/buffalo_l"
ZIP_PATH = "/app/buffalo_l.zip"
GDRIVE_FILE_ID = "1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo"

def ensure_model():
    if not os.path.exists(MODEL_DIR):
        print("📦 Model not found — downloading from Google Drive with gdown...")
        subprocess.run(["pip", "install", "--no-cache-dir", "gdown"], check=True)
        subprocess.run(["gdown", "--id", GDRIVE_FILE_ID, "-O", ZIP_PATH], check=True)

        print("✅ Download complete — extracting...")
        try:
            with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
                zip_ref.extractall(MODEL_DIR)
            print("✅ Extraction done")
        except zipfile.BadZipFile:
            print("❌ The downloaded file is not a valid ZIP file.")
            raise
    else:
        print("✅ Model already present")

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    ensure_model()
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return jsonify({'error': f'Invalid JSON: {str(e)}'}), 415

    print("✅ Received /search request")
    print(f"→ Reference images: {len(data.get('references', []))}")
    print(f"→ Thumbnails: {len(data.get('thumbnails', []))}")

    thumbnails = data.get("thumbnails", [])
    matches = []
    for thumb in thumbnails:
        if isinstance(thumb, dict):
            # Placeholder similarity; replace with real model inference
            matches.append({
                "thumbnail": thumb.get("thumbnail"),
                "post_url": thumb.get("post_url"),
                "similarity": 0.92
            })
            print(f"📌 Match: {thumb.get('thumbnail')} → 0.92")

    return jsonify({"matches": matches})

if __name__ == '__main__':
    ensure_model()
    app.run(host="0.0.0.0", port=8080)
