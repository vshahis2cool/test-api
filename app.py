import os
from flask import Flask, jsonify, request, url_for, send_file
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'images')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_authorized(req: request) -> bool:
    """Simple shared-secret check via header."""
    return req.headers.get("X-Admin-Secret") == ADMIN_PASSWORD

# -------------------------
# Backend state (learning-purpose only)
# -------------------------
current_image = "grant-and-marsh-army.png"

# -------------------------
# Serve the HTML page
# -------------------------
@app.route("/")
def index():
    return send_file("index.html")

# -------------------------
# REST API: Get current image
# -------------------------
@app.route("/api/image", methods=["GET"])
def get_image():
    return jsonify({
        "image_url": url_for('static', filename=f"images/{current_image}", _external=True)
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
        "image_url": url_for('static', filename=f"images/{current_image}", _external=True)
    })

    return jsonify({"message": "Image updated"})

# -------------------------
# REST API: Get all images
# -------------------------
@app.route("/api/images", methods=["GET"])
def list_images():
    images_dir = app.config['UPLOAD_FOLDER']
    images = [f for f in os.listdir(images_dir) if allowed_file(f)]
    return jsonify({
        "images": images,
        "current": current_image
    })

# -------------------------
# REST API: Login (shared password)
# -------------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    password = data.get("password")

    if password != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    # For this simple flow, the token is the shared secret itself
    return jsonify({"token": ADMIN_PASSWORD})

# -------------------------
# REST API: Upload image
# -------------------------
@app.route("/api/upload", methods=["POST"])
def upload_image():
    global current_image

    if not is_authorized(request):
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Automatically switch to the newly uploaded image
        current_image = filename
        
        # Notify all clients
        socketio.emit("image_updated", {
            "image_url": url_for('static', filename=f"images/{current_image}", _external=True)
        })
        
        return jsonify({
            "message": "Image uploaded successfully",
            "filename": filename,
            "image_url": url_for('static', filename=f"images/{filename}", _external=True)
        }), 201
    
    return jsonify({"error": "Invalid file type"}), 400

# -------------------------
# Start server
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, debug=True, port=port)
