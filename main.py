from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import zipfile

app = Flask(__name__)
CORS(app)

MODEL_DIR = "/app/buffalo_l"
ZIP_PATH = "/app/buffalo_l.zip"
GDRIVE_FILE_ID = "1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo"

def ensure_model():
    if not os.path.exists(MODEL_DIR):
        print("📦 Model not found — downloading from Google Drive with gdown...")
        # Ensure gdown is installed
        subprocess.run(["pip", "install", "--no-cache-dir", "gdown"], check=True)

        # Download the file using gdown
        subprocess.run(["gdown", "--id", GDRIVE_FILE_ID, "-O", ZIP_PATH], check=True)

        print("✅ Download complete — extracting...")
        try:
            with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
                zip_ref.extractall(MODEL_DIR)
            print("✅ Extraction done")
        except zipfile.BadZipFile:
            print("❌ The downloaded file is not a valid ZIP file. Please check the Google Drive link and permissions.")
            raise
    else:
        print("✅ Model already present")

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    ensure_model()

    data = request.get_json()
    print("✅ Received /search request")
    print("→ Reference images:", len(data.get("references", [])))
    print("→ Thumbnails:", len(data.get("thumbnails", [])))

    # Dummy response for now
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
