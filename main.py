from flask import Flask, request, jsonify from flask_cors import CORS import onnxruntime as ort import numpy as np import base64 import cv2 import os from insightface.app import FaceAnalysis

app = Flask(name) CORS(app, resources={r"/": {"origins": ""}})

face_app = None

@app.before_first_request def load_model(): global face_app print("🔄 Loading face analysis model...") face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']) face_app.prepare(ctx_id=0) print("✅ Model ready")

def get_embedding_from_base64(b64): try: img_bytes = base64.b64decode(b64) img_np = np.frombuffer(img_bytes, dtype=np.uint8) img = cv2.imdecode(img_np, cv2.IMREAD_COLOR) faces = face_app.get(img) if faces: return faces[0].embedding.tolist() else: return None except Exception as e: print("❌ Embedding extraction error:", e) return None

def cosine_similarity(vec1, vec2): v1 = np.array(vec1) v2 = np.array(vec2) return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

@app.route('/health') def health(): return "ok"

@app.route('/search', methods=['POST']) def search(): data = request.get_json() print("✅ Received /search request") references = data.get("references", []) thumbnails = data.get("thumbnails", [])

print("→ Reference images:", len(references))
print("→ Thumbnails:", len(thumbnails))

ref_embeddings = []
for ref in references:
    emb = get_embedding_from_base64(ref['data'])
    if emb:
        ref_embeddings.append(emb)

matches = []
for t in thumbnails:
    try:
        # Download image from URL
        resp = cv2.VideoCapture(t)
        if not resp.isOpened():
            print("❌ Cannot open thumbnail:", t)
            continue
        ret, frame = resp.read()
        if not ret:
            print("❌ Failed to read thumbnail:", t)
            continue
        faces = face_app.get(frame)
        if not faces:
            continue
        emb = faces[0].embedding.tolist()
        best_sim = 0
        for ref_emb in ref_embeddings:
            sim = cosine_similarity(emb, ref_emb)
            if sim > best_sim:
                best_sim = sim
        matches.append({
            "thumbnail": t,
            "post_url": t,
            "similarity": best_sim
        })
    except Exception as e:
        print("❌ Error processing thumbnail:", t, e)

return jsonify({"matches": matches})

if name == 'main': app.run(host="0.0.0.0", port=8080)

