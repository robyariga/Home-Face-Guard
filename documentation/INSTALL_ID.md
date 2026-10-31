# Instalasi HomeFace Guard

Prototipe eksperimental; jangan gunakan sebagai kunci pintu atau satu-satunya pengaman.
Lisensi belum ditetapkan; lihat `LICENSING.md`.

1. Pasang Python 3.13 dan Git, lalu salin repositori.
2. Dari root, buat lingkungan: `python -m venv .venv`.
3. PowerShell: `.\.venv\Scripts\Activate.ps1`. Linux/macOS: `. .venv/bin/activate`.
4. Jalankan `python -m pip install -r backend/requirements.txt`.
5. Masuk `cd backend`, jalankan `python -m flask --app app.main:create_app create-admin`.
   Isi nama, email dan password 12–128 karakter. Registrasi internet ditutup.
6. Jalankan `python run.py`; buka `http://127.0.0.1:5000/login.html`.

UI ada di `docs/`, dilayani bersama API. Jangan jalankan frontend terpisah.
Status login localStorage dan API lama yang terbuka tidak lagi didukung.

Tambahkan penghuni dari pengaturan. Dapatkan persetujuan sebelum mengunggah wajah atau
mengaktifkan kamera. Foto pendaftaran harus berisi satu wajah saja. Scan mengambil 50
sampel bertahap; jumlah sampel bukan bukti akurasi. Perhatikan peringatan training.
Jika model belum siap, hasil tidak diterima sebagai penghuni. Snapshot mati secara
bawaan; log disimpan maksimal 7 hari.

Untuk akses jaringan, baca `DEPLOYMENT.md`: perlu HTTPS, hostname yang diizinkan dan
pembatasan akses. Jalankan satu proses server. Untuk instalasi lama, buat cadangan
privat saat server mati, baca migrasi, lalu latih ulang model `labels.pkl` lama.
