"""
COMPREHENSIVE TEST FOR PHOTOBOOTH v3.0
Tests all functions without GUI
"""
import sys
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

sys.path.insert(0, r"D:\PROJECT\PROJECT PRIBADI\PHOTOBOOTH_APK")

PASSED = 0
FAILED = 0

def test(name, ok, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name} {detail}")

# ═══════════════════════════════════════════════════════
print("\n=== 1. SYNTAX & IMPORT TEST ===")
# ═══════════════════════════════════════════════════════
try:
    import py_compile
    py_compile.compile(r"D:\PROJECT\PROJECT PRIBADI\PHOTOBOOTH_APK\main.py", doraise=True)
    test("main.py syntax", True)
except Exception as e:
    test("main.py syntax", False, str(e))

from main import PhotoboothApp, ToggleButton, ColorPicker, FilterCard, log_error
test("Import all classes", True)

# ═══════════════════════════════════════════════════════
print("\n=== 2. CAMERA TEST ===")
# ═══════════════════════════════════════════════════════
cameras_found = []
for i in range(10):
    try:
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cameras_found.append((i, w, h))
                test(f"Camera {i} ({w}x{h})", True)
            else:
                test(f"Camera {i} read fail", False)
            cap.release()
    except Exception as e:
        pass

if not cameras_found:
    test("At least 1 camera", False, "No cameras found!")
else:
    test(f"Found {len(cameras_found)} camera(s)", True)

# ═══════════════════════════════════════════════════════
print("\n=== 3. FILTER TEST ===")
# ═══════════════════════════════════════════════════════
# Create mock frame
mock_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

# We need an app instance to test filters - use a mock approach
class MockApp:
    current_filter = "Normal"
    current_frame_color = "White"
    thickness_var = type('obj', (object,), {'get': lambda self: 5})()
    FRAME_COLORS = PhotoboothApp.FRAME_COLORS
    spacing_value = 10
    watermark_var = type('obj', (object,), {'get': lambda self: 'Date & Time'})()

mock = MockApp()

for fn in PhotoboothApp.FILTERS:
    try:
        result = PhotoboothApp.apply_filter(mock, mock_frame.copy(), fn)
        ok = result is not None and result.shape == (480, 640, 3)
        test(f"Filter: {fn}", ok)
    except Exception as e:
        test(f"Filter: {fn}", False, str(e))

# ═══════════════════════════════════════════════════════
print("\n=== 4. FRAME BORDER TEST ===")
# ═══════════════════════════════════════════════════════
for cn in ["None", "White", "Black", "Pink", "Gold", "Cyan", "Red", "Blue", "Green"]:
    try:
        mock.current_frame_color = cn
        result = PhotoboothApp.apply_frame_border(mock, mock_frame.copy())
        if cn == "None":
            test(f"Border: {cn} (no border)", result is not None)
        else:
            test(f"Border: {cn}", result is not None and result.shape == (480, 640, 3))
    except Exception as e:
        test(f"Border: {cn}", False, str(e))

# ═══════════════════════════════════════════════════════
print("\n=== 5. PHOTO LAYOUT TEST ===")
# ═══════════════════════════════════════════════════════
photos = [mock_frame.copy() for _ in range(4)]

mock.current_layout = "Strip Vert"
mock.spacing_value = 10
mock.watermark_var = type('obj', (object,), {'get': lambda self: 'Date & Time'})()
try:
    result = PhotoboothApp.build_final_image(mock, photos[:4])
    test("Layout: Strip Vert (4 photos)", result is not None and isinstance(result, Image.Image))
except Exception as e:
    test("Layout: Strip Vert", False, str(e))

mock.current_layout = "Strip Horiz"
try:
    result = PhotoboothApp.build_final_image(mock, photos[:4])
    test("Layout: Strip Horiz (4 photos)", result is not None and isinstance(result, Image.Image))
except Exception as e:
    test("Layout: Strip Horiz", False, str(e))

mock.current_layout = "Grid 2x2"
try:
    result = PhotoboothApp.build_final_image(mock, photos[:4])
    test("Layout: Grid 2x2 (4 photos)", result is not None and isinstance(result, Image.Image))
except Exception as e:
    test("Layout: Grid 2x2", False, str(e))

mock.current_layout = "Single"
try:
    result = PhotoboothApp.build_final_image(mock, photos[:1])
    test("Layout: Single (1 photo)", result is not None and isinstance(result, Image.Image))
except Exception as e:
    test("Layout: Single", False, str(e))

# Test with fewer photos
mock.current_layout = "Strip Vert"
try:
    result = PhotoboothApp.build_final_image(mock, photos[:2])
    test("Layout: Strip Vert (2 photos)", result is not None)
except Exception as e:
    test("Layout: Strip Vert (2)", False, str(e))

try:
    result = PhotoboothApp.build_final_image(mock, photos[:3])
    test("Layout: Strip Vert (3 photos)", result is not None)
except Exception as e:
    test("Layout: Strip Vert (3)", False, str(e))

# ═══════════════════════════════════════════════════════
print("\n=== 6. SPACING TEST ===")
# ═══════════════════════════════════════════════════════
mock.current_layout = "Strip Vert"
for sp in [0, 5, 10, 20, 50]:
    mock.spacing_value = sp
    try:
        result = PhotoboothApp.build_final_image(mock, photos[:4])
        w, h = result.size
        test(f"Spacing {sp}px -> size {w}x{h}", result is not None)
    except Exception as e:
        test(f"Spacing {sp}px", False, str(e))

# Auto spacing
for count in [1, 2, 3, 4]:
    for layout in ["Strip Vert", "Strip Horiz", "Grid 2x2", "Single"]:
        auto = PhotoboothApp._auto_spacing(mock, count, layout)
        test(f"Auto spacing: {count} photos, {layout} = {auto}px", auto >= 0)

# ═══════════════════════════════════════════════════════
print("\n=== 7. WATERMARK TEST ===")
# ═══════════════════════════════════════════════════════
test_img = Image.new("RGB", (640, 480), (100, 100, 100))
for wm in ["None", "Date & Time", "Custom Text", "Logo"]:
    mock.watermark_var = type('obj', (object,), {'get': lambda self, v=wm: v})()
    try:
        result = PhotoboothApp._add_watermark(mock, test_img.copy())
        test(f"Watermark: {wm}", result is not None)
    except Exception as e:
        test(f"Watermark: {wm}", False, str(e))

# ═══════════════════════════════════════════════════════
print("\n=== 8. SAVE TEST ===")
# ═══════════════════════════════════════════════════════
test_dir = r"D:\PROJECT\PROJECT PRIBADI\PHOTOBOOTH_APK\photos"
os.makedirs(test_dir, exist_ok=True)
test_img = Image.new("RGB", (640, 480), (255, 100, 100))
test_path = os.path.join(test_dir, "_test_save.png")
try:
    test_img.save(test_path, quality=95)
    exists = os.path.exists(test_path)
    test("Save PNG file", exists)
    if exists:
        with Image.open(test_path) as loaded:
            test("Load saved file", loaded.size == (640, 480))
        os.remove(test_path)
        test("Cleanup test file", True)
except Exception as e:
    test("Save file", False, str(e))

# ═══════════════════════════════════════════════════════
print("\n=== 9. GALLERY TEST ===")
# ═══════════════════════════════════════════════════════
# Create temp images
for i in range(3):
    test_img.save(os.path.join(test_dir, f"_gallery_test_{i}.png"))
try:
    files = [f for f in os.listdir(test_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg')) and f.startswith("_gallery")]
    test(f"Gallery: {len(files)} test files found", len(files) == 3)
except Exception as e:
    test("Gallery test", False, str(e))
# Cleanup
for f in os.listdir(test_dir):
    if f.startswith("_gallery"):
        os.remove(os.path.join(test_dir, f))

# ═══════════════════════════════════════════════════════
print("\n=== 10. CRASH LOG TEST ===")
# ═══════════════════════════════════════════════════════
try:
    log_error(Exception("Test error - ignore"))
    with open(r"D:\PROJECT\PROJECT PRIBADI\PHOTOBOOTH_APK\crash.log", "r") as f:
        content = f.read()
    test("crash.log written", "Test error - ignore" in content)
    # Remove test error
    lines = content.split("\n")
    lines = [l for l in lines if "Test error" not in l]
    with open(r"D:\PROJECT\PROJECT PRIBADI\PHOTOBOOTH_APK\crash.log", "w") as f:
        f.write("\n".join(lines))
    test("crash.log cleanup", True)
except Exception as e:
    test("crash.log", False, str(e))

# ═══════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════
total = PASSED + FAILED
print(f"\n{'='*50}")
print(f"RESULTS: {PASSED}/{total} passed, {FAILED} failed")
print(f"{'='*50}")
if FAILED == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"WARNING: {FAILED} test(s) failed!")
