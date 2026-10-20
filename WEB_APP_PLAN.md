# PHOTOBOOTH_APK v4.0 - Local Web App Plan

## Tujuan
Mengembangkan aplikasi Photobooth menjadi local web app agar UI lebih fleksibel dan mudah dicoba, tetapi tetap berjalan lokal di laptop/PC Windows.

Akses aplikasi nantinya:

```text
http://localhost:5000
```

Data tetap lokal:

- kamera dari device lokal
- hasil foto di folder `photos/`
- database SQLite di `database/photobooth.db`
- settings lokal di `config/settings.json`

## Rekomendasi Stack

### Backend
- Python
- Flask
- OpenCV
- Pillow
- NumPy
- SQLite

### Frontend
Tahap awal:

- HTML
- CSS
- JavaScript vanilla
- Bootstrap atau Tailwind CDN lokal/opsional

Tahap lanjut:

- React/Vite jika UI sudah mulai kompleks

## Prinsip Migrasi

1. Jangan langsung menghapus aplikasi Tkinter.
2. Web app dibuat paralel agar fitur lama tetap aman.
3. Kamera/capture diuji bertahap.
4. Backend harus tetap bisa berjalan tanpa internet.
5. Semua file hasil foto tetap disimpan lokal.
6. SQLite tetap dipakai untuk session history.
7. UI dibuat modular agar banyak desain bisa dicoba.

## Struktur Target

```text
PHOTOBOOTH_APK/
│
├── main.py                  # Tkinter existing, tetap dipertahankan dulu
├── web_app.py               # Entry point local web app
├── requirements.txt
│
├── app/
│   ├── database.py
│   ├── settings.py
│   ├── qr.py
│   ├── printer.py
│   ├── templates.py
│   ├── frames.py
│   ├── camera_web.py        # service kamera untuk web
│   ├── capture_web.py       # workflow capture web
│   └── image_engine.py      # filter/layout/watermark reusable
│
├── web/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── capture.html
│   │   ├── editor.html
│   │   ├── gallery.html
│   │   └── admin.html
│   │
│   └── static/
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   ├── camera.js
│       │   ├── capture.js
│       │   ├── editor.js
│       │   └── gallery.js
│       └── img/
│
├── photos/
├── database/
├── config/
├── run.bat
├── run_web.bat
└── README_WEB.md
```

## Workflow Web Target

```text
WELCOME
  ↓
NEW SESSION
  ↓
SELECT TEMPLATE
  ↓
CAMERA PREVIEW
  ↓
CAPTURE
  ↓
PHOTO EDITOR
  ↓
FINAL PREVIEW
  ↓
SAVE / PRINT
  ↓
QR CODE / SHARE LOCAL
  ↓
SESSION GALLERY
  ↓
NEW SESSION
```

## TODO Roadmap

### FASE WEB 1 - Setup Dasar

- [ ] Tambah dependency Flask di `requirements.txt`
- [ ] Buat `web_app.py`
- [ ] Buat folder `web/templates`
- [ ] Buat folder `web/static/css`
- [ ] Buat folder `web/static/js`
- [ ] Buat halaman `index.html`
- [ ] Buat `run_web.bat`
- [ ] Jalankan local server di `http://localhost:5000`

### FASE WEB 2 - Kamera Web

- [ ] Buat `app/camera_web.py`
- [ ] Endpoint `/video_feed` untuk live preview MJPEG
- [ ] Endpoint `/api/cameras` untuk scan kamera
- [ ] Endpoint `/api/camera/select` untuk pilih kamera
- [ ] Error handling jika kamera tidak tersedia
- [ ] Tombol refresh kamera di UI

### FASE WEB 3 - Capture Workflow

- [ ] Endpoint `/api/session/new`
- [ ] Endpoint `/api/capture/start`
- [ ] Endpoint `/api/capture/take`
- [ ] Countdown di frontend
- [ ] Flash effect di frontend
- [ ] Simpan foto sementara per session
- [ ] Support AUTO/MANUAL mode

### FASE WEB 4 - Editor

- [ ] Pindahkan image processing reusable ke `app/image_engine.py`
- [ ] Endpoint `/api/editor/preview`
- [ ] Pilih filter
- [ ] Pilih frame
- [ ] Atur spacing
- [ ] Pilih template
- [ ] Tambah watermark text
- [ ] Final preview

### FASE WEB 5 - Save, QR, Print

- [ ] Endpoint `/api/save`
- [ ] Simpan metadata ke SQLite
- [ ] Generate QR local URL
- [ ] Tampilkan QR di halaman hasil
- [ ] Endpoint `/api/print`
- [ ] Print file dari backend Windows

### FASE WEB 6 - Gallery

- [ ] Halaman gallery
- [ ] Filter Today
- [ ] All Photos
- [ ] Search Session ID
- [ ] Preview foto
- [ ] Delete foto
- [ ] Reprint
- [ ] Generate QR ulang

### FASE WEB 7 - Admin

- [ ] Admin login PIN
- [ ] Camera settings
- [ ] Template manager
- [ ] Printer settings
- [ ] Storage settings
- [ ] App settings
- [ ] Session history

## Catatan Penggunaan Web App

### Install dependency

```bat
C:\Users\Binta\AppData\Local\Programs\Python\Python311\python.exe -m pip install -r requirements.txt
```

### Jalankan Tkinter existing

```bat
run.bat
```

### Jalankan Web App nanti

```bat
run_web.bat
```

Atau manual:

```bat
C:\Users\Binta\AppData\Local\Programs\Python\Python311\python.exe web_app.py
```

Lalu buka browser:

```text
http://localhost:5000
```

Jika ingin dibuka dari HP dalam Wi-Fi yang sama:

```text
http://IP-LAPTOP:5000
```

Contoh:

```text
http://172.16.61.53:5000
```

## Catatan Penting

- Browser tidak boleh langsung mengakses kamera OpenCV Python; kamera dikelola backend.
- Live preview paling stabil menggunakan MJPEG streaming dari Flask.
- Untuk touchscreen, UI web lebih mudah dibuat besar dan responsif.
- Mode local artinya tidak butuh internet dan tidak upload ke cloud.
- QR Code bisa diarahkan ke local server, bukan internet.
- Kalau ingin QR bisa dibuka HP, HP harus satu jaringan Wi-Fi dengan laptop.

## Keputusan Saat Ini

Rekomendasi implementasi pertama:

```text
Flask + HTML/CSS/JS sederhana
```

Alasan:

- paling cepat dibuat
- dependency tidak banyak
- mudah debug
- cocok untuk local-only app
- fitur Tkinter lama masih bisa dipertahankan

## Risiko Teknis

- Browser/antivirus/firewall bisa memblok akses dari HP ke laptop.
- Kamera hanya bisa dipakai satu proses; jangan jalankan Tkinter dan Web camera bersamaan.
- Printing dari browser tetap harus lewat backend Python agar bisa pakai printer Windows.
- Jika pakai QR local, link hanya aktif selama server local web app berjalan.
