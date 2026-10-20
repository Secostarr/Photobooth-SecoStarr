"""Frame Manager for Photobooth v4.0 FASE 2. Handles solid colors and image overlays."""
import os
import cv2

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES_DIR = os.path.join(BASE, "assets", "frames")

SOLID_COLORS = {
    "White": (255, 255, 255), "Black": (0, 0, 0), "Pink": (255, 105, 180),
    "Gold": (255, 215, 0), "Cyan": (0, 255, 255), "Red": (255, 50, 50),
    "Blue": (50, 100, 255), "Green": (50, 200, 50),
}


def get_available_frames():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    frames = list(SOLID_COLORS.keys())
    try:
        for f in os.listdir(FRAMES_DIR):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                frames.append(f)
    except Exception:
        pass
    return frames


def apply_frame(image_bgr, frame_name, thickness=5):
    """Applies a solid border or image overlay frame."""
    if not frame_name or frame_name == "None":
        return image_bgr

    # Solid Color
    if frame_name in SOLID_COLORS:
        c = SOLID_COLORS[frame_name]
        h, w = image_bgr.shape[:2]
        return cv2.rectangle(
            image_bgr.copy(), (thickness, thickness),
            (w - thickness, h - thickness),
            (c[2], c[1], c[0]), thickness
        )
    
    # Image Overlay (not fully implemented in FASE 2, fallback to original)
    return image_bgr
