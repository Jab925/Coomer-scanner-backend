import onnxruntime
import numpy as np
import cv2
import base64
import requests
from insightface.app import FaceAnalysis
from insightface.model_zoo import model_zoo
from numpy.linalg import norm

# Load InsightFace ONNX model once
app = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
app.prepare(ctx_id=0)

def get_embedding_from_image(img_bytes):
    try:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        faces = app.get(img)
        if not faces:
            return None
        return faces[0].embedding
    except Exception as e:
        print(f"[ERROR] Failed to process image: {e}")
        return None

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

def find_matches(references, thumbnails, threshold=0.35):
    print("🔍 Matching against references...")

    # Convert all reference base64 images into embeddings
    ref_embeddings = []
    for ref in references:
        try:
            img_data = base64.b64decode(ref['data'])
            emb = get_embedding_from_image(img_data)
            if emb is not None:
                ref_embeddings.append((ref['name'], emb))
            else:
                print(f"[WARN] No face found in {ref['name']}")
        except Exception as e:
            print(f"[ERROR] Base64 decoding failed for {ref['name']}: {e}")

    if not ref_embeddings:
        print("❌ No valid reference embeddings found")
        return []

    results = []
    for thumb_url in thumbnails:
        try:
            res = requests.get(thumb_url, timeout=10)
            if res.status_code != 200:
                continue
            thumb_emb = get_embedding_from_image(res.content)
            if thumb_emb is None:
                continue

            for name, ref_emb in ref_embeddings:
                sim = cosine_similarity(ref_emb, thumb_emb)
                if sim >= threshold:
                    results.append({
                        "thumbnail": thumb_url,
                        "post_url": extract_post_url(thumb_url),
                        "similarity": round(sim, 4)
                    })
                    break  # only need one match per image
        except Exception as e:
            print(f"[ERROR] Failed to fetch thumbnail {thumb_url}: {e}")
    return results

def extract_post_url(thumb_url):
    # Dummy extractor – you can improve this logic based on real patterns
    return "https://coomer.su/post/" + thumb_url.split("/")[-1].split(".")[0]
