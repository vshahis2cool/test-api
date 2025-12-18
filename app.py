from flask import Flask, jsonify, request
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# -------------------------
# Backend state (learning-purpose only)
# -------------------------
current_image = "MARSH-JOCKEY.png"

# -------------------------
# REST API: Get current image
# -------------------------
@app.route("/api/image", methods=["GET"])
def get_image():
    return jsonify({
        "image_url": f"/static/images/{current_image}"
    })

# -------------------------
# REST API: Update image
# -------------------------
@app.route("/api/image", methods=["POST"])
def update_image():
    global current_image

    data = request.get_json()
    new_image = data.get("image")

    if not new_image:
        return jsonify({"error": "No image provided"}), 400

    current_image = new_image

    # 🔥 Push update to all connected clients
    socketio.emit("image_updated", {
        "image_url": f"/static/images/{current_image}"
    })

    return jsonify({"message": "Image updated"})

# -------------------------
# Start server
# -------------------------
if __name__ == "__main__":
    socketio.run(app, debug=True)
