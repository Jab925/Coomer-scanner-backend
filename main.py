from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import os
import search_coomer

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Set up logging
log_file = "logs.txt"
logging.basicConfig(
    filename=log_file,
    filemode='a',
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

@app.route('/health')
def health():
    return "ok"

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()

    # Logging input details
    references = data.get("references", [])
    thumbnails = data.get("thumbnails", [])
    logging.info(f"✅ /search called")
    logging.info(f"→ Reference images: {len(references)}")
    logging.info(f"→ Thumbnails: {len(thumbnails)}")

    # Call actual match function
    try:
        match_type = "face+tattoo"
        thumb_data = jsonify([
            {"thumbnail": t, "post": t} for t in thumbnails
        ]).data.decode("utf-8")

        matches = search_coomer.find_matches(references, thumb_data, match_type, threshold=0.6)

        logging.info(f"→ Matches found: {len(matches)}")
        return jsonify({"matches": matches})

    except Exception as e:
        logging.error(f"❌ Error processing /search: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/logs')
def get_logs():
    if not os.path.exists(log_file):
        return "Log file not found.", 404
    return send_file(log_file, mimetype='text/plain')

if __name__ == '__main__':
    logging.info("🚀 Backend started")
    app.run(host="0.0.0.0", port=8080)
