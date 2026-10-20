"""QR Code generation and local sharing server for Photobooth v4.0."""
import os
import socket
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import qrcode
from PIL import Image

_SERVER_THREAD = None
_SERVER_PORT = 8088
_PHOTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "photos")


def get_local_ip():
    """Get the local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


class _PhotosHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=_PHOTOS_DIR, **kwargs)

    def log_message(self, format, *args):
        # Silence standard console logs
        pass


def start_sharing_server(port=_SERVER_PORT, photos_dir=_PHOTOS_DIR):
    """Start local HTTP server in background thread if not already running."""
    global _SERVER_THREAD, _PHOTOS_DIR
    _PHOTOS_DIR = photos_dir
    os.makedirs(_PHOTOS_DIR, exist_ok=True)

    if _SERVER_THREAD is not None and _SERVER_THREAD.is_alive():
        return f"http://{get_local_ip()}:{port}"

    def run():
        try:
            httpd = HTTPServer(('0.0.0.0', port), _PhotosHTTPHandler)
            httpd.serve_forever()
        except Exception:
            pass

    _SERVER_THREAD = threading.Thread(target=run, daemon=True)
    _SERVER_THREAD.start()
    return f"http://{get_local_ip()}:{port}"


def generate_qr(data, size=(200, 200)):
    """Generate a QR code PIL image for a given URL or text."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    if size:
        img = img.resize(size, Image.LANCZOS)
    return img


def get_photo_share_url(filename, port=_SERVER_PORT):
    """Get sharing URL for a specific photo file."""
    start_sharing_server(port)
    ip = get_local_ip()
    return f"http://{ip}:{port}/{filename}"
