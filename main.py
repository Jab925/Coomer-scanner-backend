import os
import urllib.request
import zipfile

from insightface.app import FaceAnalysis

MODEL_DIR = "/app/buffalo_l"
ZIP_PATH = "/app/buffalo_l.zip"
MODEL_URL = "https://drive.google.com/uc?export=download&id=1yxiWQzsnpmh9DLO5R6CNaH4vmhYXmOYo"

def ensure_model():
    if not os.path.exists(MODEL_DIR):
        print("🔹 buffalo_l not found — downloading...")
        urllib.request.urlretrieve(MODEL_URL, ZIP_PATH)
        print("✅ Download complete — extracting...")
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall("/app")
        print("✅ Extraction done!")
    else:
        print("✅ buffalo_l already exists — skipping download.")

# Run the model setup
ensure_model()

# Now set up FaceAnalysis
print("🔹 Initializing FaceAnalysis...")
app = FaceAnalysis(name=MODEL_DIR, providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)
print("✅ FaceAnalysis ready!")

# Your app logic would go here — e.g. starting Flask, processing images
