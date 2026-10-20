import cv2
import sys

print("=== KAMERA TEST ===")
print(f"OpenCV version: {cv2.__version__}")
print()

# Test semua backend
backends = [
    ("CAP_DSHOW", cv2.CAP_DSHOW),
    ("CAP_MSMF", cv2.CAP_MSMF),
    ("DEFAULT", 0),
]

cam = None
used_backend = None

for name, backend in backends:
    print(f"Trying {name}...")
    try:
        cap = cv2.VideoCapture(0, backend)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"  OK! Resolution: {w}x{h}, FPS: {fps}")
                cam = cap
                used_backend = name
                break
            else:
                print(f"  Opened but can't read frame")
                cap.release()
        else:
            print(f"  Can't open")
            cap.release()
    except Exception as e:
        print(f"  Error: {e}")

if cam is None:
    print("\nERROR: Tidak ada kamera yang bisa dipakai!")
    sys.exit(1)

print(f"\nUsing: {used_backend}")
print("Tekan 'Q' untuk keluar dari preview\n")

while True:
    ret, frame = cam.read()
    if not ret:
        print("Can't read frame!")
        break

    frame = cv2.flip(frame, 1)
    cv2.putText(frame, f"Backend: {used_backend} | Press Q to quit", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow("KAMERA TEST", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
print("Kamera test selesai!")
