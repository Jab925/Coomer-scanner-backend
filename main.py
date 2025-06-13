from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # ✅ Allow all origins for CORS

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    print("✅ Received /search request")
    print("→ Reference images:", len(data.get("references", [])))
    print("→ Thumbnails:", len(data.get("thumbnails", [])))

    # Dummy response until real match logic is integrated
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
    app.run(host="0.0.0.0", port=8080)
