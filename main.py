from flask import Flask, request, jsonify
from flask_cors import CORS
from insightface.app import FaceAnalysis
import numpy as np
import cv2
import base64
import requests

app = Flask(__name__)
CORS(app)

face_app = FaceAnalysis(name="buffalo_l", root="/app/buffalo_l")
face_app.prepare(ctx_id=0)

def decode_base64_img(b64_data):
    img_data = base64.b64decode(b64_data)
    np_arr = np.frombuffer(img_data, np.uint8)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json(force=True)
    refs = []
    for ref in data.get("references", []):
        img = decode_base64_img(ref["data"])
        faces = face_app.get(img)
        if faces:
            refs.append(faces[0].normed_embedding)

    matches = []
    for thumb in data.get("thumbnails", []):
        resp = requests.get(thumb["thumbnail"])
        img = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)
        faces = face_app.get(img)
        if not faces:
            continue
        emb = faces[0].normed_embedding
        sim = max(np.dot(emb, ref) for ref in refs)
        matches.append({
            "thumbnail": thumb["thumbnail"],
            "post_url": thumb.get("post_url"),
            "similarity": float(round(sim, 4))
        })

    return jsonify({"matches": matches})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
