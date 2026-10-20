import cv2
import sys

print("=== KAMERA TEST (headless) ===\n")

backends = [
    ("CAP_DSHOW", cv2.CAP_DSHOW),
    ("CAP_MSMF", cv2.CAP_MSMF),
    ("DEFAULT(0)", 0),
]

for name, backend in backends:
    print(f"Testing {name}...")
    try:
        cap = cv2.VideoCapture(0, backend)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"  OK! {w}x{h} FPS={fps} FrameShape={frame.shape}")
            else:
                print(f"  Opened but FAILED to read frame")
            cap.release()
        else:
            print(f"  FAILED to open")
    except Exception as e:
        print(f"  EXCEPTION: {e}")

print("\nTest selesai.")
