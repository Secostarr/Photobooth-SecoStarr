"""
PHOTOBOOTH DESKTOP APPLICATION v3.0
=====================================
Interactive UI with Photo Spacing Controls
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from datetime import datetime
import os
import math

try:
    from app.database import init_db, next_session_id, create_session, update_session, add_photo
    from app.settings import load_settings, save_settings
    try:
        from app import templates as app_templates
        from app import frames as app_frames
        from app import qr as app_qr
        from app import printer as app_printer
    except Exception:
        app_templates = None
        app_frames = None
        app_qr = None
        app_printer = None
    _V4_MODULES = True
except Exception:
    _V4_MODULES = False
    app_templates = None
    app_frames = None
    app_qr = None
    app_printer = None

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")

def log_error(e):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {type(e).__name__}: {e}\n")


class ToggleButton(tk.Canvas):
    """Animated toggle switch widget"""
    def __init__(self, parent, text="", command=None, width=50, height=26, **kw):
        super().__init__(parent, width=width, height=height, highlightthickness=0,
                         bg=kw.get("bg", "#16213e"), cursor="hand2")
        self._on = False
        self._cmd = command
        self._text = text
        self._btn_w = width
        self._btn_h = height
        self._pos = 3
        self.bind("<Button-1>", self._click)
        self._draw()

    def _click(self, e=None):
        self._on = not self._on
        self._animate()
        if self._cmd:
            self._cmd(self._on)

    def _animate(self):
        target = self._btn_w - self._btn_h + 3 if self._on else 3
        step = 3 if target > self._pos else -3
        def loop():
            nonlocal step
            if (step > 0 and self._pos < target) or (step < 0 and self._pos > target):
                self._pos += step
                self._draw()
                self.after(10, loop)
            else:
                self._pos = target
                self._draw()
        loop()

    def _draw(self):
        self.delete("all")
        bg = "#e94560" if self._on else "#333355"
        self._rounded_rect(0, 0, self._btn_w, self._btn_h, 13, fill=bg, outline="")
        self.create_oval(self._pos, 3, self._pos + self._btn_h - 6, self._btn_h - 3, fill="white", outline="")
        if self._text:
            self.create_text(self._btn_w // 2, self._btn_h // 2, text=self._text, fill="white",
                             font=("Segoe UI", 7, "bold"))

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
               x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def get(self):
        return self._on


class ColorPicker(tk.Canvas):
    """Clickable color swatch"""
    def __init__(self, parent, color, size=28, command=None, **kw):
        super().__init__(parent, width=size, height=size, highlightthickness=2,
                         highlightbackground="#16213e", bg="#16213e", cursor="hand2")
        self._color = color
        self._cmd = command
        self._size = size
        self._selected = False
        self._draw()
        self.bind("<Button-1>", self._click)

    def _click(self, e=None):
        if self._cmd:
            self._cmd(self._color)

    def _draw(self):
        self.delete("all")
        margin = 3
        self.create_rectangle(margin, margin, self._size-margin, self._size-margin,
                              fill=self._color, outline="#333" if self._color != "#000000" else "#555",
                              width=1)

    def select(self, selected=True):
        self._selected = selected
        self.configure(highlightbackground="#e94560" if selected else "#16213e",
                       highlightthickness=3 if selected else 2)


class FilterCard(tk.Canvas):
    """Clickable filter preview card with thumbnail"""
    def __init__(self, parent, name, size=70, command=None, **kw):
        super().__init__(parent, width=size, height=size + 18, highlightthickness=1,
                         highlightbackground="#0f3460", bg="#0a0a1a", cursor="hand2")
        self._name = name
        self._cmd = command
        self._size = size
        self._selected = False
        self._thumb = None
        self._draw_placeholder()
        self.bind("<Button-1>", self._click)

    def _click(self, e=None):
        if self._cmd:
            self._cmd(self._name)

    def _draw_placeholder(self):
        self.delete("all")
        icons = {"Normal": "N", "Grayscale": "G", "Sepia": "S", "Vintage": "V",
                 "Warm": "W", "Cool": "C", "B&W High": "B", "Negative": "-", "Sketch": "~"}
        icon = icons.get(self._name, "?")
        self.create_text(self._size // 2, self._size // 2, text=icon, fill="#53d8fb",
                         font=("Segoe UI", 22, "bold"))
        label = self._name[:8] if len(self._name) > 8 else self._name
        self.create_text(self._size // 2, self._size + 9, text=label, fill="#aaa",
                         font=("Segoe UI", 7))

    def update_thumb(self, pil_img):
        self._thumb = pil_img.copy().resize((self._size - 4, self._size - 4), Image.LANCZOS)
        thumb_tk = ImageTk.PhotoImage(self._thumb)
        self.delete("all")
        self.create_image(2, 2, anchor="nw", image=thumb_tk)
        self.image = thumb_tk
        label = self._name[:8]
        self.create_text(self._size // 2, self._size + 9, text=label, fill="#aaa",
                         font=("Segoe UI", 7))

    def select(self, selected=True):
        self._selected = selected
        self.configure(highlightbackground="#e94560" if selected else "#0f3460",
                       highlightthickness=3 if selected else 1)


class PhotoboothApp:
    APP_NAME = "Photobooth"
    VERSION = "4.0"
    SAVE_DIR = "photos"

    BG_DARK = "#0f0f23"
    BG_PANEL = "#16213e"
    BG_CAMERA = "#0a0a1a"
    ACCENT = "#e94560"
    ACCENT2 = "#53d8fb"
    TEXT = "#ffffff"
    TEXT_DIM = "#888899"
    BORDER = "#0f3460"

    FILTERS = ["Normal", "Grayscale", "Sepia", "Vintage", "Warm", "Cool",
               "B&W High", "Negative", "Sketch"]

    FRAME_COLORS = {
        "White": (255, 255, 255), "Black": (0, 0, 0), "Pink": (255, 105, 180),
        "Gold": (255, 215, 0), "Cyan": (0, 255, 255), "Red": (255, 50, 50),
        "Blue": (50, 100, 255), "Green": (50, 200, 50),
    }

    LAYOUTS = ["Strip Vert", "Strip Horiz", "Grid 2x2", "Single"]

    def __init__(self, root):
        self.root = root
        self.root.title(f"{self.APP_NAME} v{self.VERSION}")
        self.root.configure(bg=self.BG_DARK)
        self.sw = self.root.winfo_screenwidth()
        self.sh = self.root.winfo_screenheight()
        
        # Set geometry ke pojok kanan atas
        # Default: 1280x720, posisi x = lebar_layar - 1280, y = 0
        win_w, win_h = 1280, 720
        pos_x = self.sw - win_w
        self.root.geometry(f"{win_w}x{win_h}+{pos_x}+0")

        self.settings = load_settings() if _V4_MODULES else {}
        if _V4_MODULES:
            init_db()
        self.camera = None
        self.is_running = False
        self.current_session_id = None
        self.current_filter = self.settings.get("default_filter", "Normal")
        self.current_frame_color = "White"
        self.current_template = None
        self.current_layout = self.settings.get("default_layout", "Strip Vert")
        self.captured_photos = []
        self.is_counting_down = False
        self.photo_preview_window = None
        self.cam_width = 640
        self.cam_height = 480
        self.filter_cards = []
        self.color_pickers = []

        self.spacing_auto = True
        self.spacing_value = 10
        self.available_cameras = []
        self.selected_camera_index = int(self.settings.get("default_camera", 0)) if self.settings else 0
        self.capture_mode = "auto"
        self.capture_paused = False
        self.pending_next_index = 0

        self.SAVE_DIR = self.settings.get("output_folder", self.SAVE_DIR) if self.settings else self.SAVE_DIR
        os.makedirs(self.SAVE_DIR, exist_ok=True)
        self._build_menu()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.scan_cameras()
        self.root.after(300, self.start_camera)

    # ─── MENU ─────────────────────────────────────────────
    def _build_menu(self):
        mb = tk.Menu(self.root, bg=self.BG_PANEL, fg=self.TEXT,
                     activebackground=self.ACCENT, font=("Segoe UI", 10))
        fm = tk.Menu(mb, tearoff=0, bg=self.BG_PANEL, fg=self.TEXT,
                     activebackground=self.ACCENT, font=("Segoe UI", 10))
        fm.add_command(label="Save", command=self.save_photo, accelerator="Ctrl+S")
        fm.add_command(label="Gallery", command=self.open_gallery, accelerator="Ctrl+G")
        fm.add_separator()
        fm.add_command(label="Exit", command=self.on_close)
        mb.add_cascade(label="File", menu=fm)
        em = tk.Menu(mb, tearoff=0, bg=self.BG_PANEL, fg=self.TEXT,
                     activebackground=self.ACCENT, font=("Segoe UI", 10))
        em.add_command(label="Reset All", command=self._reset_all)
        mb.add_cascade(label="Edit", menu=em)
        hm = tk.Menu(mb, tearoff=0, bg=self.BG_PANEL, fg=self.TEXT,
                      activebackground=self.ACCENT, font=("Segoe UI", 10))
        hm.add_command(label="About", command=self._show_about)
        mb.add_cascade(label="Help", menu=hm)
        self.root.config(menu=mb)
        self.root.bind("<Control-s>", lambda e: self.save_photo())
        self.root.bind("<Control-g>", lambda e: self.open_gallery())

    # ─── BUILD UI ─────────────────────────────────────────
    def _build_ui(self):
        main = tk.Frame(self.root, bg=self.BG_DARK)
        main.pack(fill="both", expand=True)

        # ── SIDEBAR ──
        sidebar = tk.Frame(main, bg=self.BG_PANEL, width=360)
        sidebar.pack(side="right", fill="y", padx=(3, 6), pady=6)
        sidebar.pack_propagate(False)

        canvas_sb = tk.Canvas(sidebar, bg=self.BG_PANEL, highlightthickness=0, bd=0)
        sb_scroll = tk.Scrollbar(sidebar, orient="vertical", command=canvas_sb.yview)
        sb_inner = tk.Frame(canvas_sb, bg=self.BG_PANEL)
        sb_inner.bind("<Configure>", lambda e: canvas_sb.configure(scrollregion=canvas_sb.bbox("all")))
        canvas_sb.create_window((0, 0), window=sb_inner, anchor="nw", width=350)
        canvas_sb.configure(yscrollcommand=sb_scroll.set)
        canvas_sb.pack(side="left", fill="both", expand=True)
        sb_scroll.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas_sb.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas_sb.bind_all("<MouseWheel>", _on_mousewheel)

        # Header
        hdr = tk.Frame(sb_inner, bg=self.BG_PANEL)
        hdr.pack(fill="x", pady=(10, 5))
        tk.Label(hdr, text=self.APP_NAME, font=("Segoe UI", 24, "bold"),
                 bg=self.BG_PANEL, fg=self.ACCENT).pack(side="left", padx=15)
        tk.Label(hdr, text=f"v{self.VERSION}", font=("Segoe UI", 10),
                 bg=self.BG_PANEL, fg=self.TEXT_DIM).pack(side="left")
        self._sep(sb_inner)

        # ── FILTER CARDS ──
        self._sec(sb_inner, "FILTERS")
        filter_frame = tk.Frame(sb_inner, bg=self.BG_PANEL)
        filter_frame.pack(fill="x", padx=10, pady=(3, 5))
        for i, fname in enumerate(self.FILTERS):
            row = i // 4
            col = i % 4
            card = FilterCard(filter_frame, fname, size=72,
                              command=self._on_filter_click)
            card.grid(row=row, column=col, padx=3, pady=3)
            self.filter_cards.append(card)
        self.filter_cards[0].select(True)

        # ── FRAME BORDER ──
        self._sec(sb_inner, "FRAME BORDER")
        fr_top = tk.Frame(sb_inner, bg=self.BG_PANEL)
        fr_top.pack(fill="x", padx=15, pady=3)
        tk.Label(fr_top, text="Color:", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 9)).pack(side="left")
        self.thickness_var = tk.IntVar(value=5)
        tk.Label(fr_top, text="  Size:", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 9)).pack(side="left", padx=(10, 0))
        tk.Spinbox(fr_top, from_=1, to=20, textvariable=self.thickness_var,
                   width=3, font=("Segoe UI", 9)).pack(side="left")

        color_row = tk.Frame(sb_inner, bg=self.BG_PANEL)
        color_row.pack(fill="x", padx=15, pady=(3, 0))
        for cn, cv in self.FRAME_COLORS.items():
            hex_color = f"#{cv[0]:02x}{cv[1]:02x}{cv[2]:02x}"
            cp = ColorPicker(color_row, hex_color, size=26,
                             command=self._on_color_click)
            cp.pack(side="left", padx=2)
            self.color_pickers.append((cn, cp))
        self.color_pickers[0][1].select(True)

        self._sep(sb_inner)

        # ── TEMPLATE ──
        self._sec(sb_inner, "TEMPLATE")
        tpl_row = tk.Frame(sb_inner, bg=self.BG_PANEL)
        tpl_row.pack(fill="x", padx=15, pady=3)
        self.template_buttons = []
        tpl_names = app_templates.TEMPLATE_NAMES if app_templates else ["Strip 4"]
        for tn in tpl_names:
            info = app_templates.get_template(tn) if app_templates else {"icon": tn[:3]}
            b = tk.Button(tpl_row, text=info.get("icon", tn[:3]),
                          font=("Segoe UI", 8, "bold"),
                          bg=self.BORDER, fg=self.TEXT, relief="flat", cursor="hand2",
                          activebackground=self.ACCENT,
                          command=lambda t=tn: self._on_template_click(t))
            b.pack(side="left", padx=1, expand=True, fill="x")
            self.template_buttons.append((tn, b))
        if self.template_buttons:
            self.template_buttons[-1][1].config(bg=self.ACCENT)

        # ── PHOTO DESIGN ──
        self._sec(sb_inner, "PHOTO DESIGN")

        # Layout
        tk.Label(sb_inner, text="Layout", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=15, pady=(5, 0))
        lf = tk.Frame(sb_inner, bg=self.BG_PANEL)
        lf.pack(fill="x", padx=15, pady=3)
        self.layout_buttons = []
        for ln in self.LAYOUTS:
            b = tk.Button(lf, text=ln.split()[0][:5], font=("Segoe UI", 8, "bold"),
                          bg=self.BORDER, fg=self.TEXT, relief="flat", cursor="hand2",
                          activebackground=self.ACCENT, command=lambda l=ln: self._on_layout_click(l))
            b.pack(side="left", padx=1, expand=True, fill="x")
            self.layout_buttons.append((ln, b))
        self.layout_buttons[0][1].config(bg=self.ACCENT)

        # ── SPACING CONTROL ──
        tk.Label(sb_inner, text="Photo Spacing", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=15, pady=(8, 0))

        spacing_frame = tk.Frame(sb_inner, bg=self.BG_PANEL)
        spacing_frame.pack(fill="x", padx=15, pady=3)

        self.spacing_toggle = ToggleButton(spacing_frame, text="Auto", command=self._on_spacing_toggle,
                                           width=70, height=26, bg=self.BG_PANEL)
        self.spacing_toggle.pack(side="left")
        self.spacing_toggle._on = True
        self.spacing_toggle._draw()

        self.spacing_slider_label = tk.Label(spacing_frame, text="10px", bg=self.BG_PANEL,
                                              fg=self.ACCENT2, font=("Segoe UI", 9, "bold"), width=5)
        self.spacing_slider_label.pack(side="right")

        self.spacing_slider = tk.Scale(sb_inner, from_=0, to=50, orient="horizontal",
                                        variable=tk.IntVar(value=10), bg=self.BG_PANEL, fg=self.TEXT,
                                        highlightthickness=0, troughcolor=self.BORDER,
                                        sliderrelief="flat", length=280,
                                        command=self._on_spacing_change)
        self.spacing_slider.set(10)
        self.spacing_slider.config(state="disabled")
        self.spacing_slider.pack(padx=15, fill="x")

        # ── PHOTO COUNT + WATERMARK ──
        top_row = tk.Frame(sb_inner, bg=self.BG_PANEL)
        top_row.pack(fill="x", padx=15, pady=(5, 0))

        tk.Label(top_row, text="Count", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(side="left")
        self.photo_count_var = tk.IntVar(value=int(self.settings.get("default_photo_count", 4)) if self.settings else 4)
        count_f = tk.Frame(top_row, bg=self.BG_PANEL)
        count_f.pack(side="left", padx=(5, 0))
        for n in [1, 2, 3, 4]:
            tk.Radiobutton(count_f, text=str(n), variable=self.photo_count_var, value=n,
                           bg=self.BG_PANEL, fg=self.TEXT, selectcolor=self.BORDER,
                           activebackground=self.BG_PANEL, font=("Segoe UI", 10),
                           indicatoron=0, padx=8, pady=2).pack(side="left", padx=1)

        tk.Label(top_row, text="Watermark", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(side="left", padx=(12, 0))
        self.watermark_var = tk.StringVar(value="Date & Time")
        ttk.Combobox(top_row, textvariable=self.watermark_var,
                     values=["None", "Date & Time", "Custom Text", "Logo"],
                     state="readonly", width=12).pack(side="left", padx=3)

        # ── COUNTDOWN ──
        tk.Label(sb_inner, text="Countdown", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=15, pady=(8, 0))
        cd_f = tk.Frame(sb_inner, bg=self.BG_PANEL)
        cd_f.pack(fill="x", padx=15, pady=3)
        self.cd_var = tk.IntVar(value=int(self.settings.get("default_countdown", 3)) if self.settings else 3)
        for val in [2, 3, 5]:
            tk.Radiobutton(cd_f, text=f"{val}s", variable=self.cd_var, value=val,
                           bg=self.BG_PANEL, fg=self.TEXT, selectcolor=self.BORDER,
                           activebackground=self.BG_PANEL, font=("Segoe UI", 10),
                           indicatoron=0, padx=12, pady=3).pack(side="left", padx=2)

        # ── CAPTURE MODE ──
        tk.Label(sb_inner, text="Capture Mode", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=15, pady=(8, 0))
        cm_f = tk.Frame(sb_inner, bg=self.BG_PANEL)
        cm_f.pack(fill="x", padx=15, pady=3)

        self.capture_mode_label = tk.Label(cm_f, text="AUTO", font=("Segoe UI", 9, "bold"),
                                            bg=self.BG_PANEL, fg=self.ACCENT2, width=8)
        self.capture_mode_label.pack(side="left")

        self.capture_toggle = ToggleButton(cm_f, text="", command=self._on_capture_toggle,
                                           width=50, height=26, bg=self.BG_PANEL)
        self.capture_toggle.pack(side="left", padx=5)
        self.capture_toggle._on = False
        self.capture_toggle._draw()

        self._sep(sb_inner)

        # ── CAPTURE BUTTON ──
        self.capture_btn = tk.Button(sb_inner, text="CAPTURE", font=("Segoe UI", 18, "bold"),
                                      bg=self.ACCENT, fg="white", activebackground="#c81e45",
                                      activeforeground="white", relief="flat", cursor="hand2",
                                      command=self.start_capture, height=2)
        self.capture_btn.pack(fill="x", padx=15, pady=(5, 5))

        # ── NEXT PHOTO BUTTON (shown in manual mode) ──
        self.next_btn = tk.Button(sb_inner, text="NEXT PHOTO >", font=("Segoe UI", 14, "bold"),
                                   bg="#27ae60", fg="white", activebackground="#219a52",
                                   activeforeground="white", relief="flat", cursor="hand2",
                                   command=self._on_next_photo, height=2)
        self.next_btn.pack(fill="x", padx=15, pady=(0, 5))
        self.next_btn.pack_forget()

        btn_row = tk.Frame(sb_inner, bg=self.BG_PANEL)
        btn_row.pack(fill="x", padx=15, pady=(0, 3))
        self.save_btn = tk.Button(btn_row, text="Save", font=("Segoe UI", 10, "bold"),
                                   bg=self.BORDER, fg=self.ACCENT2, relief="flat", cursor="hand2",
                                   command=self.save_photo, state="disabled")
        self.save_btn.pack(side="left", expand=True, fill="x", padx=(0, 2))
        self.gallery_btn = tk.Button(btn_row, text="Gallery", font=("Segoe UI", 10, "bold"),
                                      bg=self.BORDER, fg=self.ACCENT2, relief="flat", cursor="hand2",
                                      command=self.open_gallery)
        self.gallery_btn.pack(side="left", expand=True, fill="x", padx=(2, 0))

        # Thumbnails
        self._sec(sb_inner, "CAPTURED")
        self.thumb_canvas = tk.Canvas(sb_inner, bg=self.BG_CAMERA, height=85, highlightthickness=0)
        self.thumb_canvas.pack(fill="x", padx=15, pady=(3, 15))

        # ── CAMERA ──
        cam_frame = tk.Frame(main, bg=self.BG_PANEL)
        cam_frame.pack(side="left", fill="both", expand=True, padx=(6, 3), pady=6)

        cam_header = tk.Frame(cam_frame, bg=self.BORDER)
        cam_header.pack(fill="x")
        tk.Label(cam_header, text="  LIVE CAMERA", font=("Segoe UI", 12, "bold"),
                 bg=self.BORDER, fg=self.ACCENT2).pack(side="left", pady=6)

        cam_ctrl = tk.Frame(cam_header, bg=self.BORDER)
        cam_ctrl.pack(side="right", padx=10)

        self.cam_status = tk.Label(cam_ctrl, text="Starting...", font=("Segoe UI", 9),
                                    bg=self.BORDER, fg=self.TEXT_DIM)
        self.cam_status.pack(side="right", padx=(0, 8))

        self.cam_select_var = tk.StringVar(value="Scanning...")
        self.cam_select_cb = ttk.Combobox(cam_ctrl, textvariable=self.cam_select_var,
                                           values=["Scanning..."], state="readonly", width=25)
        self.cam_select_cb.pack(side="right")
        self.cam_select_cb.bind("<<ComboboxSelected>>", self._on_camera_change)

        tk.Button(cam_ctrl, text="Refresh", font=("Segoe UI", 7), bg=self.BORDER, fg=self.ACCENT2,
                  relief="flat", cursor="hand2", command=self.scan_cameras,
                  activebackground=self.ACCENT).pack(side="right", padx=(0, 5))

        self.camera_label = tk.Label(cam_frame, bg="#000", text="Starting camera...",
                                      font=("Segoe UI", 16), fg="#555")
        self.camera_label.pack(fill="both", expand=True, padx=3, pady=(3, 0))

        self.countdown_label = tk.Label(cam_frame, text="", font=("Segoe UI", 120, "bold"),
                                         bg="#0a0a1a", fg=self.ACCENT)

        # Status
        self.status_var = tk.StringVar(value="Ready")
        sb = tk.Frame(self.root, bg=self.BORDER, height=28)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        tk.Label(sb, textvariable=self.status_var, bg=self.BORDER, fg=self.TEXT_DIM,
                 font=("Segoe UI", 9), anchor="w", padx=10).pack(fill="both", expand=True)

    def _sep(self, p):
        tk.Frame(p, bg=self.BORDER, height=1).pack(fill="x", padx=15, pady=4)

    def _sec(self, p, t):
        f = tk.Frame(p, bg=self.BG_PANEL)
        f.pack(fill="x", padx=15, pady=(8, 2))
        tk.Label(f, text=t, font=("Segoe UI", 8, "bold"), bg=self.BG_PANEL,
                 fg=self.ACCENT2).pack(side="left")
        tk.Frame(f, bg=self.BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(5, 0))

    # ─── EVENT HANDLERS ───────────────────────────────────
    def _on_filter_click(self, name):
        self.current_filter = name
        for card in self.filter_cards:
            card.select(card._name == name)
        self.status_var.set(f"Filter: {name}")

    def _on_color_click(self, color_name):
        self.current_frame_color = color_name
        for cn, cp in self.color_pickers:
            cp.select(cn == color_name)

    def _on_layout_click(self, name):
        self.current_layout = name
        for ln, b in self.layout_buttons:
            b.config(bg=self.ACCENT if ln == name else self.BORDER)

    def _on_template_click(self, name):
        if not app_templates:
            return
        tpl = app_templates.get_template(name)
        self.current_template = name
        for tn, b in self.template_buttons:
            b.config(bg=self.ACCENT if tn == name else self.BORDER)
        if hasattr(self, "photo_count_var"):
            self.photo_count_var.set(tpl["photo_count"])
        self._on_layout_click(tpl["layout"])
        self.status_var.set(f"Template: {name} ({tpl['description']})")

    def _on_spacing_toggle(self, is_auto):
        self.spacing_auto = is_auto
        if is_auto:
            self.spacing_slider.config(state="disabled")
            auto_val = self._auto_spacing(self.photo_count_var.get(), self.current_layout)
            self.spacing_slider.set(auto_val)
            self.spacing_slider_label.config(text=f"{auto_val}px")
            self.spacing_value = auto_val
        else:
            self.spacing_slider.config(state="normal")
            self.spacing_value = self.spacing_slider.get()

    def _on_spacing_change(self, val):
        self.spacing_value = int(val)
        self.spacing_slider_label.config(text=f"{val}px")

    def _auto_spacing(self, count, layout):
        if layout == "Single":
            return 0
        elif count == 1:
            return 15
        elif count == 2:
            return 12
        elif count == 3:
            return 10
        else:
            return 8

    def _reset_all(self):
        self.current_filter = "Normal"
        self.current_frame_color = "White"
        self.current_layout = "Strip Vert"
        self.capture_mode = "auto"
        self.capture_toggle._on = False
        self.capture_toggle._draw()
        self.capture_mode_label.config(text="AUTO", fg="#53d8fb")
        self.filter_var = "Normal"
        for card in self.filter_cards:
            card.select(card._name == "Normal")
        for cn, cp in self.color_pickers:
            cp.select(cn == "White")
        for ln, b in self.layout_buttons:
            b.config(bg=self.ACCENT if ln == "Strip Vert" else self.BORDER)
        self.next_btn.pack_forget()
        self.status_var.set("All settings reset")

    def _show_about(self):
        messagebox.showinfo("About",
            f"{self.APP_NAME} v{self.VERSION}\n\n"
            "Desktop Photo Studio\n"
            "Python + Tkinter + OpenCV\n\n"
            "Features:\n"
            "- Live Camera with 9 Filters\n"
            "- 8 Frame Border Colors\n"
            "- 4 Photo Layouts\n"
            "- Adjustable Photo Spacing\n"
            "- Watermark & Date Stamp\n"
            "- Gallery Viewer")

    # ─── CAMERA ───────────────────────────────────────────
    def scan_cameras(self):
        self.cam_status.config(text="Scanning...")
        self.root.update_idletasks()
        self.available_cameras = []
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, test = cap.read()
                    name = cap.getBackendName()
                    if ret and test is not None:
                        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        cam_name = f"Camera {i} ({w}x{h})"
                    else:
                        cam_name = f"Camera {i}"
                    cap.release()
                    self.available_cameras.append((i, cam_name))
                else:
                    cap.release()
            except Exception:
                pass

        names = [c[1] for c in self.available_cameras]
        if not names:
            names = ["No camera found"]
        self.cam_select_cb.config(values=names)
        if self.available_cameras:
            selected = next((c for c in self.available_cameras if c[0] == self.selected_camera_index), self.available_cameras[0])
            self.selected_camera_index = selected[0]
            self.cam_select_var.set(selected[1])
        else:
            self.cam_select_var.set(names[0])
        self.status_var.set(f"Found {len(self.available_cameras)} camera(s)")

    def _on_camera_change(self, event=None):
        sel = self.cam_select_var.get()
        for idx, name in self.available_cameras:
            if name == sel:
                self.selected_camera_index = idx
                break
        self._switch_camera()

    def _switch_camera(self):
        if self.camera and self.camera.isOpened():
            self.is_running = False
            self.camera.release()
            self.camera = None
        self.start_camera()

    def start_camera(self):
        self.cam_status.config(text="Opening...")
        self.root.update_idletasks()
        self.camera = None
        idx = self.selected_camera_index
        try:
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_height)
                self.camera = cap
        except Exception as e:
            log_error(e)
        if self.camera is None:
            try:
                cap = cv2.VideoCapture(idx)
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_height)
                    self.camera = cap
            except Exception as e:
                log_error(e)
        if self.camera is None:
            self.camera_label.configure(text="Kamera tidak ditemukan!")
            self.cam_status.config(text="NO CAMERA", fg="#ff4444")
            return
        self.is_running = True
        self.cam_status.config(text="Active", fg="#44ff44")
        self.status_var.set(f"Camera {idx} active!")
        self.update_frame()

    def update_frame(self):
        if not self.is_running:
            return
        try:
            ret, frame = self.camera.read()
            if ret:
                frame = cv2.flip(frame, 1)
                self.cam_width = frame.shape[1]
                self.cam_height = frame.shape[0]
                filtered = self.apply_filter(frame.copy(), self.current_filter)
                filtered = self.apply_frame_border(filtered)
                rgb = cv2.cvtColor(filtered, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                w = self.camera_label.winfo_width()
                h = self.camera_label.winfo_height()
                if w > 10 and h > 10:
                    img = img.resize((w, h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.camera_label.configure(image=photo, text="")
                self.camera_label.image = photo
        except Exception as e:
            log_error(e)
        self.root.after(50, self.update_frame)

    # ─── FILTERS ──────────────────────────────────────────
    def apply_filter(self, frame, fn):
        if not fn or fn == "Normal":
            return frame
        try:
            if fn == "Grayscale":
                return cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
            elif fn == "Sepia":
                k = np.array([[0.272,0.534,0.131],[0.349,0.686,0.168],[0.393,0.769,0.189]])
                return np.clip(cv2.transform(frame, k), 0, 255).astype(np.uint8)
            elif fn == "Vintage":
                k = np.array([[0.393,0.769,0.189],[0.349,0.686,0.168],[0.272,0.534,0.131]])
                v = np.clip(cv2.transform(frame, k), 0, 255).astype(np.uint8)
                h, w = frame.shape[:2]
                Y, X = np.ogrid[:h, :w]
                cx, cy = w//2, h//2
                vig = np.clip(1 - (np.sqrt((X-cx)**2+(Y-cy)**2)/np.sqrt(cx**2+cy**2))*0.5, 0, 1)
                return (v * np.stack([vig]*3, axis=-1)).astype(np.uint8)
            elif fn == "Warm":
                b, g, r = cv2.split(frame)
                return cv2.merge((b, g, cv2.add(r, 25)))
            elif fn == "Cool":
                b, g, r = cv2.split(frame)
                return cv2.merge((cv2.add(b, 25), g, r))
            elif fn == "B&W High":
                g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, bw = cv2.threshold(g, 128, 255, cv2.THRESH_BINARY)
                return cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)
            elif fn == "Negative":
                return 255 - frame
            elif fn == "Sketch":
                g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                inv = 255 - g
                blur = cv2.GaussianBlur(inv, (21, 21), 0)
                return cv2.cvtColor(cv2.divide(g, 255 - blur, scale=256), cv2.COLOR_GRAY2BGR)
        except Exception:
            pass
        return frame

    def apply_frame_border(self, frame):
        cn = self.current_frame_color
        c = self.FRAME_COLORS.get(cn)
        if not c:
            return frame
        t = self.thickness_var.get()
        return cv2.rectangle(frame, (t, t), (frame.shape[1]-t, frame.shape[0]-t), (c[2], c[1], c[0]), t)

    # ─── CAPTURE ──────────────────────────────────────────
    def _on_capture_toggle(self, is_manual):
        self.capture_mode = "manual" if is_manual else "auto"
        if is_manual:
            self.capture_mode_label.config(text="MANUAL", fg="#e94560")
        else:
            self.capture_mode_label.config(text="AUTO", fg="#53d8fb")
        self.status_var.set(f"Capture mode: {self.capture_mode.upper()}")

    def _set_capture_mode(self, mode):
        self.capture_mode = mode
        if mode == "auto":
            self.capture_toggle._on = False
            self.capture_toggle._draw()
            self.capture_mode_label.config(text="AUTO", fg="#53d8fb")
        else:
            self.capture_toggle._on = True
            self.capture_toggle._draw()
            self.capture_mode_label.config(text="MANUAL", fg="#e94560")

    def _on_next_photo(self):
        if self.capture_paused:
            self.capture_paused = False
            self.next_btn.pack_forget()
            self.capture_btn.config(state="disabled")
            idx = self.pending_next_index
            self.root.after(300, lambda: self._capture_loop(idx))

    def start_capture(self):
        if self.is_counting_down:
            return
        if not self.camera or not self.camera.isOpened():
            messagebox.showerror("Camera Error", "Kamera belum aktif. Pilih/refresh kamera lalu coba lagi.")
            self.status_var.set("Camera not active")
            return
        self.current_session_id = next_session_id() if _V4_MODULES else datetime.now().strftime("SESSION-%Y%m%d-%H%M%S")
        if _V4_MODULES:
            create_session(self.current_session_id, self.photo_count_var.get(), self.current_layout,
                           self.current_filter, self.current_layout)
        self.captured_photos = []
        self.update_thumbnails()
        self.save_btn.config(state="disabled")
        self.next_btn.pack_forget()
        self.status_var.set(f"Session: {self.current_session_id}")
        self._capture_loop(0)

    def _capture_loop(self, index):
        count = self.photo_count_var.get()
        if index >= count:
            self.is_counting_down = False
            self.capture_btn.config(state="normal")
            self.next_btn.pack_forget()
            if self.captured_photos:
                self.save_btn.config(state="normal")
                self.status_var.set("Capture complete!")
                self.show_preview()
            return

        self.is_counting_down = True
        self.capture_btn.config(state="disabled")
        self.status_var.set(f"Photo {index+1}/{count}")
        self._do_countdown(self.cd_var.get(), lambda i=index: self._take_photo(i))

    def _take_photo(self, index):
        if not self.camera or not self.camera.isOpened():
            self.is_counting_down = False
            self.capture_btn.config(state="normal")
            self.status_var.set("Capture failed: camera not active")
            messagebox.showerror("Camera Error", "Kamera tidak aktif saat capture.")
            return
        ret, frame = self.camera.read()
        if ret and frame is not None:
            frame = cv2.flip(frame, 1)
            filtered = self.apply_filter(frame, self.current_filter)
            filtered = self.apply_frame_border(filtered)
            self.captured_photos.append(filtered)
            self.update_thumbnails()
            self.status_var.set(f"Photo {index+1}/{self.photo_count_var.get()} captured!")
        else:
            self.is_counting_down = False
            self.capture_btn.config(state="normal")
            self.status_var.set("Capture failed: cannot read camera frame")
            messagebox.showerror("Camera Error", "Gagal membaca frame kamera.")
            return

        count = self.photo_count_var.get()
        next_index = index + 1

        if next_index >= count:
            self.root.after(400, lambda: self._capture_loop(next_index))
        elif self.capture_mode == "manual":
            self.capture_paused = True
            self.pending_next_index = next_index
            self.is_counting_down = False
            self.capture_btn.config(state="normal")
            remaining = count - next_index
            self.next_btn.config(text=f"NEXT PHOTO ({remaining} left)")
            self.next_btn.pack(fill="x", padx=15, pady=(0, 5), after=self.capture_btn)
            self.status_var.set(f"Manual: click NEXT PHOTO ({remaining} remaining)")
        else:
            self.root.after(400, lambda: self._capture_loop(next_index))

    def _do_countdown(self, secs, cb):
        if secs <= 0:
            self.countdown_label.place_forget()
            cb()
            return
        self.countdown_label.configure(text=str(secs))
        self.countdown_label.place(relx=0.5, rely=0.5, anchor="center")
        self.root.after(1000, lambda: self._do_countdown(secs - 1, cb))

    # ─── PHOTO DESIGN ENGINE ──────────────────────────────
    def build_final_image(self, photos):
        layout = self.current_layout
        count = len(photos)
        if layout == "Single":
            return PhotoboothApp._compose_single(self, photos[0])
        elif layout == "Strip Vert":
            return PhotoboothApp._compose_strip(self, photos, "vertical")
        elif layout == "Strip Horiz":
            return PhotoboothApp._compose_strip(self, photos, "horizontal")
        elif layout == "Grid 2x2":
            return PhotoboothApp._compose_grid(self, photos)
        return PhotoboothApp._compose_strip(self, photos, "vertical")

    def _compose_single(self, photo_bgr):
        img = Image.fromarray(cv2.cvtColor(photo_bgr, cv2.COLOR_BGR2RGB))
        return PhotoboothApp._add_watermark(self, img)

    def _compose_strip(self, photos, direction):
        pw, ph = 640, 480
        sp = self.spacing_value
        n = len(photos)
        if direction == "vertical":
            tw = pw + sp * 2
            th = (ph + sp) * n + sp
        else:
            tw = (pw + sp) * n + sp
            th = ph + sp * 2

        strip = Image.new("RGB", (tw, th), (255, 255, 255))
        for i, p in enumerate(photos):
            img = Image.fromarray(cv2.cvtColor(p, cv2.COLOR_BGR2RGB)).resize((pw, ph), Image.LANCZOS)
            if direction == "vertical":
                x, y = sp, sp + i * (ph + sp)
            else:
                x, y = sp + i * (pw + sp), sp
            strip.paste(img, (x, y))

        return PhotoboothApp._add_watermark(self, strip)

    def _compose_grid(self, photos):
        pw, ph = 640, 480
        sp = self.spacing_value
        while len(photos) < 4:
            photos.append(photos[-1] if photos else np.zeros((ph, pw, 3), np.uint8))
        pw2 = (pw - sp) // 2
        ph2 = (ph - sp) // 2
        tw = pw2 * 2 + sp * 3
        th = ph2 * 2 + sp * 3
        grid = Image.new("RGB", (tw, th), (255, 255, 255))
        pos = [(sp, sp), (sp+pw2+sp, sp), (sp, sp+ph2+sp), (sp+pw2+sp, sp+ph2+sp)]
        for i in range(4):
            img = Image.fromarray(cv2.cvtColor(photos[i], cv2.COLOR_BGR2RGB)).resize((pw2, ph2), Image.LANCZOS)
            grid.paste(img, pos[i])
        return PhotoboothApp._add_watermark(self, grid)

    def _add_watermark(self, img):
        wm = self.watermark_var.get()
        if not wm or wm == "None":
            return img
        draw = ImageDraw.Draw(img)
        w, h = img.size
        try:
            font = ImageFont.truetype("arial.ttf", max(18, h // 28))
        except Exception:
            font = ImageFont.load_default()
        text = datetime.now().strftime("%d/%m/%Y %H:%M") if wm == "Date & Time" else wm
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = h - (bbox[3] - bbox[1]) - 15
        draw.text((x+2, y+2), text, fill=(0, 0, 0, 128), font=font)
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        return img

    # ─── THUMBNAILS ───────────────────────────────────────
    def update_thumbnails(self):
        self.thumb_canvas.delete("all")
        x = 5
        for i, p in enumerate(self.captured_photos[-6:]):
            rgb = cv2.cvtColor(p, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb).resize((55, 40), Image.LANCZOS)
            ph = ImageTk.PhotoImage(img)
            self.thumb_canvas.image = ph
            self.thumb_canvas.create_image(x, 5, anchor="nw", image=ph)
            self.thumb_canvas.create_text(x+27, 52, text=f"#{i+1}", fill=self.ACCENT2,
                                           font=("Segoe UI", 7))
            x += 62

    # ─── PREVIEW / PHOTO EDITOR ───────────────────────────
    def show_preview(self):
        if not self.captured_photos:
            return
        if self.photo_preview_window and self.photo_preview_window.winfo_exists():
            self.photo_preview_window.destroy()

        win = tk.Toplevel(self.root)
        win.title("Photo Editor")
        win.configure(bg=self.BG_DARK)
        self.photo_preview_window = win

        self._editor_final = None
        self._editor_photo = None

        body = tk.Frame(win, bg=self.BG_DARK)
        body.pack(fill="both", expand=True)

        preview_holder = tk.Frame(body, bg=self.BG_DARK)
        preview_holder.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self._editor_label = tk.Label(preview_holder, bg=self.BG_DARK)
        self._editor_label.pack(expand=True)

        editor = tk.Frame(body, bg=self.BG_PANEL, width=260)
        editor.pack(side="right", fill="y", padx=(0, 10), pady=10)
        editor.pack_propagate(False)

        tk.Label(editor, text="EDITOR", font=("Segoe UI", 14, "bold"),
                 bg=self.BG_PANEL, fg=self.ACCENT2).pack(pady=(10, 4))

        tk.Label(editor, text="Filter", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12)
        self._ed_filter = tk.StringVar(value=self.current_filter)
        ttk.Combobox(editor, textvariable=self._ed_filter, values=self.FILTERS,
                     state="readonly", width=22).pack(padx=12, pady=2)
        self._ed_filter.trace_add("write", lambda *a: self._rebuild_editor_preview())

        tk.Label(editor, text="Frame Color", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(8, 0))
        self._ed_frame = tk.StringVar(value=self.current_frame_color)
        ttk.Combobox(editor, textvariable=self._ed_frame, values=["None"] + list(self.FRAME_COLORS.keys()),
                     state="readonly", width=22).pack(padx=12, pady=2)
        self._ed_frame.trace_add("write", lambda *a: self._rebuild_editor_preview())

        tk.Label(editor, text="Spacing", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(8, 0))
        self._ed_spacing = tk.IntVar(value=self.spacing_value)
        tk.Scale(editor, from_=0, to=50, orient="horizontal", variable=self._ed_spacing,
                 bg=self.BG_PANEL, fg=self.TEXT, highlightthickness=0,
                 troughcolor=self.BORDER, length=220,
                 command=lambda v: self._rebuild_editor_preview()).pack(padx=12)

        tk.Label(editor, text="Custom Watermark", bg=self.BG_PANEL, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(8, 0))
        self._ed_watermark = tk.StringVar(value="")
        e = tk.Entry(editor, textvariable=self._ed_watermark, width=24)
        e.pack(padx=12, pady=2)
        e.bind("<KeyRelease>", lambda ev: self._rebuild_editor_preview())

        bf = tk.Frame(editor, bg=self.BG_PANEL)
        bf.pack(side="bottom", fill="x", pady=12, padx=10)
        tk.Button(bf, text="Save", font=("Segoe UI", 10, "bold"), bg=self.ACCENT, fg="white",
                  command=self._editor_save, relief="flat", cursor="hand2").pack(fill="x", pady=2)
        self._qr_btn = tk.Button(bf, text="QR Share", font=("Segoe UI", 10), bg=self.BORDER, fg=self.ACCENT2,
                                  relief="flat", cursor="hand2", command=self._show_qr_overlay)
        self._qr_btn.pack(fill="x", pady=2)
        self._qr_btn.pack_forget()
        tk.Button(bf, text="Print", font=("Segoe UI", 10), bg=self.BORDER, fg=self.ACCENT2,
                  command=self._editor_print, relief="flat", cursor="hand2").pack(fill="x", pady=2)
        tk.Button(bf, text="Retake", font=("Segoe UI", 10), bg=self.BORDER, fg=self.ACCENT2,
                  command=win.destroy, relief="flat", cursor="hand2").pack(fill="x", pady=2)

        self._rebuild_editor_preview()

        win.update_idletasks()
        w = min(int(self.sw * 0.85), 1200)
        h = min(int(self.sh * 0.85), 900)
        win.geometry(f"{w}x{h}+{(self.sw-w)//2}+{(self.sh-h)//2}")

    def _build_edited_image(self):
        old_filter, old_frame, old_spacing = self.current_filter, self.current_frame_color, self.spacing_value
        old_wm = self.watermark_var.get()
        self.current_filter = self._ed_filter.get()
        self.current_frame_color = self._ed_frame.get()
        self.spacing_value = self._ed_spacing.get()
        custom = self._ed_watermark.get().strip()
        if custom:
            self.watermark_var.set(custom)
        photos = []
        for p in self.captured_photos:
            q = self.apply_filter(p.copy(), self.current_filter)
            q = self.apply_frame_border(q)
            photos.append(q)
        final = self.build_final_image(photos)
        self.current_filter, self.current_frame_color, self.spacing_value = old_filter, old_frame, old_spacing
        self.watermark_var.set(old_wm)
        return final

    def _rebuild_editor_preview(self):
        if not (self.photo_preview_window and self.photo_preview_window.winfo_exists()):
            return
        final = self._build_edited_image()
        self._editor_final = final
        display = final.copy()
        mh = int(self.sh * 0.72)
        mw = int(self.sw * 0.55)
        if display.height > mh:
            r = mh / display.height
            display = display.resize((int(display.width * r), mh), Image.LANCZOS)
        if display.width > mw:
            r = mw / display.width
            display = display.resize((int(display.width * r), int(display.height * r)), Image.LANCZOS)
        photo = ImageTk.PhotoImage(display)
        self._editor_photo = photo
        self._editor_label.configure(image=photo)

    def _editor_save(self):
        final = self._build_edited_image()
        self.current_filter = self._ed_filter.get()
        self.current_frame_color = self._ed_frame.get()
        self.spacing_value = self._ed_spacing.get()
        fp = self._save_image(final)
        if fp and hasattr(self, "_qr_btn"):
            self._last_saved_path = fp
            self._qr_btn.pack(fill="x", pady=2)

    def _show_qr_overlay(self):
        if not hasattr(self, "_last_saved_path") or not os.path.exists(self._last_saved_path):
            messagebox.showwarning("QR Code", "Simpan foto terlebih dahulu sebelum membuat QR code!")
            return
        if not app_qr:
            messagebox.showerror("Error", "Modul QR tidak tersedia.")
            return

        filename = os.path.basename(self._last_saved_path)
        url = app_qr.get_photo_share_url(filename)
        qr_img = app_qr.generate_qr(url, size=(250, 250))

        win = tk.Toplevel(self.root)
        win.title("Scan QR Code")
        win.configure(bg=self.BG_DARK)
        win.geometry("320x380")

        tk.Label(win, text="SCAN TO DOWNLOAD", font=("Segoe UI", 12, "bold"),
                 bg=self.BG_DARK, fg=self.ACCENT).pack(pady=(15, 5))
        
        photo = ImageTk.PhotoImage(qr_img)
        lbl = tk.Label(win, image=photo, bg=self.BG_DARK)
        lbl.image = photo
        lbl.pack(pady=10)

        tk.Label(win, text=url, font=("Segoe UI", 8), bg=self.BG_DARK,
                 fg=self.ACCENT2, wraplength=280).pack(pady=5)
        tk.Button(win, text="Tutup", font=("Segoe UI", 9), bg=self.BORDER, fg=self.TEXT,
                  relief="flat", cursor="hand2", command=win.destroy).pack(pady=10)

    def _editor_print(self):
        final = self._build_edited_image()
        # Save temporary image if not already saved
        if not hasattr(self, "_last_saved_path") or not os.path.exists(self._last_saved_path):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = os.path.join(self.SAVE_DIR, f"print_temp_{ts}.png")
            final.save(temp_path)
            target = temp_path
        else:
            target = self._last_saved_path

        if app_printer:
            ok, msg = app_printer.print_photo(target)
            if ok:
                messagebox.showinfo("Print", "Perintah cetak berhasil dikirim!")
            else:
                messagebox.showwarning("Print", f"Gagal mencetak: {msg}")
        else:
            messagebox.showwarning("Print", "Modul printer tidak tersedia.")

    # ─── SAVE / GALLERY ──────────────────────────────────
    def save_photo(self):
        if not self.captured_photos:
            messagebox.showwarning("Warning", "No photos to save!")
            return
        self._save_image(self.build_final_image(self.captured_photos))

    def _save_image(self, image):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fp = filedialog.asksaveasfilename(
            initialdir=os.path.abspath(self.SAVE_DIR), initialfile=f"photobooth_{ts}",
            defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if fp:
            image.save(fp, quality=95)
            if _V4_MODULES and self.current_session_id:
                file_name = os.path.basename(fp)
                update_session(self.current_session_id, photo_count=len(self.captured_photos),
                               template=self.current_layout, filter=self.current_filter,
                               layout=self.current_layout, file_name=file_name, file_path=fp)
                add_photo(self.current_session_id, file_name, fp)
            self.status_var.set(f"Saved: {os.path.basename(fp)}")
            messagebox.showinfo("Saved", f"Photo saved!\n{fp}")
            return fp
        return None

    def open_gallery(self):
        win = tk.Toplevel(self.root)
        win.title("Gallery")
        win.configure(bg=self.BG_DARK)
        win.geometry(f"{int(self.sw*0.7)}x{int(self.sh*0.7)}+{int(self.sw*0.15)}+{int(self.sh*0.15)}")

        tk.Label(win, text="GALLERY", font=("Segoe UI", 18, "bold"),
                 bg=self.BG_DARK, fg=self.ACCENT).pack(pady=(10, 4))

        ctrl = tk.Frame(win, bg=self.BG_DARK)
        ctrl.pack(fill="x", padx=10, pady=4)

        self._gal_scope = tk.StringVar(value="all")
        for label, val in [("Today", "today"), ("All Photos", "all")]:
            tk.Radiobutton(ctrl, text=label, variable=self._gal_scope, value=val,
                           bg=self.BG_DARK, fg=self.TEXT, selectcolor=self.BORDER,
                           activebackground=self.BG_DARK, font=("Segoe UI", 10),
                           indicatoron=0, padx=12, pady=3,
                           command=self._reload_gallery).pack(side="left", padx=4)

        tk.Label(ctrl, text="Session ID:", bg=self.BG_DARK, fg=self.TEXT_DIM,
                 font=("Segoe UI", 9)).pack(side="left", padx=(20, 2))
        self._gal_search = tk.StringVar()
        e = tk.Entry(ctrl, textvariable=self._gal_search, width=26)
        e.pack(side="left")
        e.bind("<Return>", lambda ev: self._reload_gallery())
        tk.Button(ctrl, text="Search", font=("Segoe UI", 9, "bold"), bg=self.BORDER,
                  fg=self.ACCENT2, relief="flat", cursor="hand2",
                  command=self._reload_gallery).pack(side="left", padx=4)
        tk.Button(ctrl, text="Open Folder", font=("Segoe UI", 9), bg=self.BORDER,
                  fg=self.ACCENT2, relief="flat", cursor="hand2",
                  command=lambda: os.startfile(os.path.abspath(self.SAVE_DIR))
                  if hasattr(os, "startfile") else None).pack(side="left", padx=4)

        self._gallery_holder = tk.Frame(win, bg=self.BG_DARK)
        self._gallery_holder.pack(fill="both", expand=True, padx=5, pady=5)
        self._gal_photo_refs = []
        self._reload_gallery()

    def _gallery_files(self, scope, search):
        try:
            files = [f for f in os.listdir(self.SAVE_DIR)
                     if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        except Exception:
            files = []
        if scope == "today":
            today = datetime.now().strftime("%Y%m%d")
            files = [f for f in files if f.startswith("photobooth_") and today in f
                     or f.startswith(today)]
        if search:
            files = [f for f in files if search.lower() in f.lower()]
        return sorted(files, reverse=True)[:60]

    def _reload_gallery(self):
        if not (hasattr(self, "_gallery_holder") and self._gallery_holder.winfo_exists()):
            return
        for w in self._gallery_holder.winfo_children():
            w.destroy()
        self._gal_photo_refs = []
        files = self._gallery_files(self._gal_scope.get(), self._gal_search.get().strip())
        if not files:
            tk.Label(self._gallery_holder, text="No photos found.", bg=self.BG_DARK,
                     fg=self.TEXT_DIM, font=("Segoe UI", 12)).pack(pady=60)
            return
        canvas = tk.Canvas(self._gallery_holder, bg=self.BG_CAMERA, highlightthickness=0)
        sb = tk.Scrollbar(self._gallery_holder, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.BG_CAMERA)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        for i, fname in enumerate(files):
            try:
                path = os.path.join(self.SAVE_DIR, fname)
                img = Image.open(path)
                img.thumbnail((180, 120), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._gal_photo_refs.append(photo)
                cell = tk.Frame(inner, bg=self.BG_PANEL, bd=1, relief="ridge")
                cell.grid(row=i // 3, column=i % 3, padx=5, pady=5)
                lbl = tk.Label(cell, image=photo, bg=self.BG_PANEL, cursor="hand2")
                lbl.image = photo
                lbl.pack()
                lbl.bind("<Button-1>", lambda e, p=path: self._preview_image(p))
                tk.Label(cell, text=fname[:26], bg=self.BG_PANEL, fg=self.TEXT_DIM,
                         font=("Segoe UI", 7), wraplength=170).pack()
                row = tk.Frame(cell, bg=self.BG_PANEL)
                row.pack(pady=(0, 3))
                tk.Button(row, text="Preview", font=("Segoe UI", 7), bg=self.BORDER,
                          fg=self.ACCENT2, relief="flat", cursor="hand2",
                          command=lambda p=path: self._preview_image(p)).pack(side="left", padx=2)
                tk.Button(row, text="Reprint", font=("Segoe UI", 7), bg=self.BORDER,
                          fg=self.ACCENT2, relief="flat", cursor="hand2",
                          command=lambda p=path: self._reprint(p)).pack(side="left", padx=2)
                tk.Button(row, text="QR", font=("Segoe UI", 7), bg=self.BORDER,
                          fg=self.ACCENT2, relief="flat", cursor="hand2",
                          command=lambda p=path: self._show_gallery_qr(p)).pack(side="left", padx=2)
                tk.Button(row, text="Delete", font=("Segoe UI", 7), bg="#7a1f2b",
                          fg="white", relief="flat", cursor="hand2",
                          command=lambda p=path: self._delete_photo(p)).pack(side="left", padx=2)
            except Exception:
                continue

    def _preview_image(self, path):
        try:
            win = tk.Toplevel(self.root)
            win.title(os.path.basename(path))
            win.configure(bg=self.BG_DARK)
            img = Image.open(path)
            mh = int(self.sh * 0.8)
            mw = int(self.sw * 0.8)
            img.thumbnail((mw, mh), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(win, image=photo, bg=self.BG_DARK)
            lbl.image = photo
            lbl.pack(padx=10, pady=10)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reprint(self, path):
        if app_printer:
            ok, msg = app_printer.print_photo(path)
            if ok:
                messagebox.showinfo("Print", "Perintah cetak ulang berhasil dikirim!")
            else:
                messagebox.showwarning("Print", f"Gagal mencetak: {msg}")
        else:
            messagebox.showwarning("Print", "Modul printer tidak tersedia.")

    def _show_gallery_qr(self, path):
        if not app_qr:
            messagebox.showerror("Error", "Modul QR tidak tersedia.")
            return

        filename = os.path.basename(path)
        url = app_qr.get_photo_share_url(filename)
        qr_img = app_qr.generate_qr(url, size=(250, 250))

        win = tk.Toplevel(self.root)
        win.title("Scan QR Code")
        win.configure(bg=self.BG_DARK)
        win.geometry("320x380")

        tk.Label(win, text="SCAN TO DOWNLOAD", font=("Segoe UI", 12, "bold"),
                 bg=self.BG_DARK, fg=self.ACCENT).pack(pady=(15, 5))
        
        photo = ImageTk.PhotoImage(qr_img)
        lbl = tk.Label(win, image=photo, bg=self.BG_DARK)
        lbl.image = photo
        lbl.pack(pady=10)

        tk.Label(win, text=url, font=("Segoe UI", 8), bg=self.BG_DARK,
                 fg=self.ACCENT2, wraplength=280).pack(pady=5)
        tk.Button(win, text="Tutup", font=("Segoe UI", 9), bg=self.BORDER, fg=self.TEXT,
                  relief="flat", cursor="hand2", command=win.destroy).pack(pady=10)

    def _delete_photo(self, path):
        if not messagebox.askyesno("Delete", f"Delete {os.path.basename(path)}?"):
            return
        try:
            os.remove(path)
            self.status_var.set(f"Deleted: {os.path.basename(path)}")
            self._reload_gallery()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_close(self):
        self.is_running = False
        if _V4_MODULES:
            self.settings.update({
                "default_camera": self.selected_camera_index,
                "default_filter": self.current_filter,
                "default_layout": self.current_layout,
                "default_photo_count": self.photo_count_var.get(),
                "default_countdown": self.cd_var.get(),
                "output_folder": self.SAVE_DIR,
            })
            save_settings(self.settings)
        if self.camera and self.camera.isOpened():
            self.camera.release()
        self.root.destroy()


def main():
    try:
        root = tk.Tk()
        root.withdraw()
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        splash = tk.Toplevel(root)
        splash.overrideredirect(True)
        splash.configure(bg="#16213e")
        splash.geometry(f"400x250+{(sw-400)//2}+{(sh-250)//2}")
        sf = tk.Frame(splash, bg="#16213e")
        sf.pack(fill="both", expand=True)
        tk.Label(sf, text="PHOTOBOOTH", font=("Segoe UI", 28, "bold"),
                 bg="#16213e", fg="#e94560").pack(pady=(30, 5))
        tk.Label(sf, text="Desktop Photo Studio v3.0", font=("Segoe UI", 12),
                 bg="#16213e", fg="#53d8fb").pack()
        progress = ttk.Progressbar(sf, mode="indeterminate", length=250)
        progress.pack(pady=15)
        progress.start(15)
        tk.Label(sf, text="Loading...", font=("Segoe UI", 9), bg="#16213e", fg="#888").pack()

        def finish():
            progress.stop()
            splash.destroy()
            root.deiconify()
            PhotoboothApp(root)

        splash.after(1500, finish)
        root.mainloop()
    except Exception as e:
        log_error(e)
        try:
            messagebox.showerror("Fatal Error", f"Crash!\n{e}\n\nCek crash.log")
        except:
            pass


if __name__ == "__main__":
    main()
