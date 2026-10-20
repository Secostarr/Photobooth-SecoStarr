import cv2
import time

print("=== QUICK CAMERA TEST ===")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
print(f"Opened: {cap.isOpened()}")
if cap.isOpened():
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    for i in range(5):
        ret, f = cap.read()
        bright = f.sum() if ret and f is not None else 0
        print(f"  Frame {i}: ret={ret} shape={f.shape if f is not None else 'None'} brightness={bright}")
        time.sleep(0.1)
    cap.release()
print("Done")
