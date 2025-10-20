# 1. Pilih base image
# Gunakan base image Python yang sesuai (misalnya, Python 3.9, 3.10, dll.)
FROM python:3.10

# 2. Set direktori kerja (work directory) di dalam container
# Semua perintah selanjutnya akan dieksekusi dari direktori ini
WORKDIR /app

# 3. Salin file dependensi (requirements.txt) ke direktori kerja
# Ini penting untuk instalasi paket.
# Gunakan --chown=user jika Anda akan beralih ke non-root user (praktik keamanan yang baik).
COPY requirements.txt /app/

# 4. Instal dependensi dari requirements.txt
# Gunakan --no-cache-dir untuk menghemat ruang disk
RUN pip install --no-cache-dir -r requirements.txt

# 5. Salin semua file aplikasi Anda yang lain ke direktori kerja
# Pastikan file utama aplikasi Anda (misalnya app.py) ada di sini
COPY . /app

# (Opsional tapi disarankan untuk keamanan) Beralih ke non-root user
# Hugging Face menyarankan penggunaan non-root user di Docker Spaces
RUN useradd -m -u 1000 user
USER user

# 6. Tentukan port yang akan diekspos
# Port default di Spaces adalah 7860
ENV PORT 7860
EXPOSE 7860

# 7. Tentukan perintah yang akan dijalankan saat container dimulai
# Ganti 'python app.py' dengan perintah untuk menjalankan aplikasi Anda (misalnya uvicorn, gunicorn, atau lainnya)
# Contoh untuk aplikasi FastAPI/Uvicorn:
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
# Contoh untuk aplikasi Python sederhana:
CMD ["python", "app.py"]