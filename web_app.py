import os
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory

from app.database import init_db, next_session_id, create_session, list_sessions
from app.settings import load_settings
from app.templates import TEMPLATE_NAMES, get_template
from app.frames import get_available_frames
from app.qr import get_local_ip

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.join(BASE_DIR, "photos")

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "web", "templates"),
    static_folder=os.path.join(BASE_DIR, "web", "static"),
)

settings = load_settings()
init_db()
os.makedirs(PHOTOS_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template(
        "index.html",
        app_name="Photobooth Web",
        version="4.0 Local",
        templates=TEMPLATE_NAMES,
        frames=get_available_frames(),
        local_ip=get_local_ip(),
        year=datetime.now().year,
    )


@app.route("/capture")
def capture():
    return render_template(
        "capture.html",
        app_name="Photobooth Web",
        templates=TEMPLATE_NAMES,
        frames=get_available_frames(),
    )


@app.route("/gallery")
def gallery():
    files = sorted(
        [f for f in os.listdir(PHOTOS_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg"))],
        reverse=True,
    )[:60]
    return render_template("gallery.html", app_name="Gallery", files=files)


@app.route("/photos/<path:filename>")
def photo_file(filename):
    return send_from_directory(PHOTOS_DIR, filename)


@app.route("/api/health")
def api_health():
    return jsonify({"ok": True, "mode": "local", "version": "4.0"})


@app.route("/api/session/new", methods=["POST"])
def api_new_session():
    session_id = next_session_id()
    create_session(session_id)
    return jsonify({"ok": True, "session_id": session_id})


@app.route("/api/templates")
def api_templates():
    return jsonify({"ok": True, "templates": [get_template(name) for name in TEMPLATE_NAMES]})


@app.route("/api/frames")
def api_frames():
    return jsonify({"ok": True, "frames": get_available_frames()})


@app.route("/api/sessions")
def api_sessions():
    rows = list_sessions(100)
    data = []
    for row in rows:
        data.append({
            "session_id": row[0],
            "date": row[1],
            "time": row[2],
            "photo_count": row[3],
            "template": row[4],
            "filter": row[5],
            "layout": row[6],
            "file_name": row[7],
            "file_path": row[8],
        })
    return jsonify({"ok": True, "sessions": data})


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5000
    print(f"Photobooth Web running at http://{host}:{port}")
    print(f"LAN access if needed: http://{get_local_ip()}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)
