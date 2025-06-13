import json
import numpy as np
import cv2
import base64
from insightface.app import FaceAnalysis

# Lazy init model
app = None

def init_model():
    global app
    if app is None:
        app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        app.prepare(ctx_id=0)

def extract_embedding(img_bytes):
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    faces = app.get(img)
    if not faces:
        return None
    return faces[0].embedding

def find_matches(files, thumb_data, match_type, threshold):
    init_model()

    thumbs = json.loads(thumb_data)
    reference_embeddings = []

    # Extract embeddings from uploaded base64 images
    for f in files:
        try:
            img_bytes = base64.b64decode(f['data'])
            emb = extract_embedding(img_bytes)
            if emb is not None:
                reference_embeddings.append(emb)
        except Exception as e:
            print(f"❌ Error extracting embedding: {e}")

    if not reference_embeddings:
        return []

    matches = []
    for thumb in thumbs:
        try:
            img_url = thumb["thumbnail"]
            post_url = thumb["post"]

            # Download thumbnail
            resp = requests.get(img_url, timeout=10)
            if resp.status_code != 200:
                continue

            emb = extract_embedding(resp.content)
            if emb is None:
                continue

            # Compare against all reference embeddings
            for ref in reference_embeddings:
                sim = float(np.dot(ref, emb) / (np.linalg.norm(ref) * np.linalg.norm(emb)))
                if sim >= threshold:
                    matches.append({
                        "similarity": sim,
                        "match_type": match_type,
                        "thumbnail": img_url,
                        "post_url": post_url
                    })
                    break  # Only need 1 good match
        except Exception as e:
            print(f"❌ Error processing thumbnail: {e}")

    return matches
