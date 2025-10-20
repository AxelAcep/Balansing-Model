# ===============================
# model_api.py — Versi Aman & Optimal
# ===============================

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import os
import shutil
import tempfile
import traceback
import numpy as np
from io import BytesIO
from PIL import Image
from ultralytics import YOLO
import glob

# ===========================================
# 🔧 PERSIAPAN & PEMBERSIHAN CACHE
# ===========================================
# Bersihkan cache dan folder tmp yang sering menumpuk
shutil.rmtree("/tmp/Ultralytics", ignore_errors=True)
shutil.rmtree("/root/.cache/ultralytics", ignore_errors=True)
shutil.rmtree("/root/.cache/torch", ignore_errors=True)

# Buat folder sementara baru untuk cache YOLO
TEMP_YOLO_DIR = tempfile.mkdtemp(prefix="yolo_cache_")
os.environ["YOLO_CONFIG_DIR"] = TEMP_YOLO_DIR
os.environ["ULTRALYTICS_CACHE_DIR"] = TEMP_YOLO_DIR
os.environ["YOLO_VERBOSE"] = "False"

# ===========================================
# 🔍 LOAD MODEL YOLO SEKALI SAJA
# ===========================================
model = YOLO("best.pt")

# ===========================================
# 🔹 IMPORT MODUL & KONFIGURASI LAIN
# ===========================================
from anemia import deteksi_anemia

DATA_PATH = "antropometri_tb_u.csv"

app = FastAPI(
    title="Health Prediction API",
    description="API untuk deteksi Anemia, Stunting, dan YOLO Object Detection",
    version="1.0",
    max_request_size=5 * 1024 * 1024  # Maks upload file 5 MB
)

# ===========================================
# 📦 MODELS UNTUK REQUEST BODY
# ===========================================
class AnemiaInput(BaseModel):
    lemas: bool
    riwayat: bool
    konjungtiva: bool
    kuku: bool

class StuntingInput(BaseModel):
    usiaBulan: int
    tinggi: float
    kelamin: str


# ===========================================
# 🧼 DETEKSI SANITASI
# ===========================================
def deteksi_sanitasi(sanitasi_data: dict) -> str:
    skor = 0
    if sanitasi_data.get("sikat_gigi_harian"):
        skor += 1
    skor += sum(1 for v in sanitasi_data.get("waktu_sikat_gigi", {}).values() if v)
    if sanitasi_data.get("cuci_tangan_harian"):
        skor += 1
    skor += sum(1 for v in sanitasi_data.get("waktu_cuci_tangan", {}).values() if v)
    if sanitasi_data.get("bab_di_toilet"):
        skor += 1
    if sanitasi_data.get("air_mineral_untuk_minum_masak"):
        skor += 1

    if skor >= 10:
        return "Baik"
    elif skor >= 6:
        return "Cukup"
    else:
        return "Buruk"


# ===========================================
# 🩸 PREDIKSI ANEMIA
# ===========================================
def anemiaPrediction(lemas: bool, riwayat: bool, konjungtiva: bool, kuku: bool):
    status_anemia = deteksi_anemia(
        lemas=lemas,
        riwayat=riwayat,
        konjungtiva_pucat=konjungtiva,
        kuku_pucat=kuku
    )
    print(f"Hasil prediksi anemia: {status_anemia}")
    return status_anemia


# ===========================================
# 📏 PREDIKSI STUNTING
# ===========================================
def stuntingPrediction(usiaBulan: int, tinggi: float, kelamin: str):
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=500, detail=f"Data PMK tidak ditemukan di: {DATA_PATH}")
    
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memuat data CSV: {e}")

    baris = df[
        (df["usia_bulan"] == usiaBulan) &
        (df["jenis_kelamin"].str.upper() == kelamin.upper())
    ]

    if baris.empty:
        raise HTTPException(status_code=404, detail=f"Tidak ditemukan data PMK untuk usia {usiaBulan} bulan dan jenis kelamin {kelamin}")

    median = float(baris["median"].values[0])
    minus_1sd = float(baris["minus_1sd"].values[0])
    sd = median - minus_1sd
    z_score = (tinggi - median) / sd

    if z_score < -3:
        status = "Sangat Pendek"
    elif -3 <= z_score < -2:
        status = "Pendek"
    elif -2 <= z_score <= 3:
        status = "Normal"
    else:
        status = "Tinggi"

    return status


def stuntingPrediction2(usiaBulan: int, tinggi: float, kelamin: str):
    # versi yang mengembalikan z-score mentah
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=500, detail=f"Data PMK tidak ditemukan di: {DATA_PATH}")

    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memuat data CSV: {e}")

    baris = df[
        (df["usia_bulan"] == usiaBulan) &
        (df["jenis_kelamin"].str.upper() == kelamin.upper())
    ]

    if baris.empty:
        raise HTTPException(status_code=404, detail=f"Tidak ditemukan data PMK untuk usia {usiaBulan} bulan dan jenis kelamin {kelamin}")

    median = float(baris["median"].values[0])
    minus_1sd = float(baris["minus_1sd"].values[0])
    sd = median - minus_1sd
    z_score = (tinggi - median) / sd
    print("Z-Score:", z_score)
    return z_score


# ===========================================
# 🚀 ENDPOINTS
# ===========================================
@app.post("/anemia", status_code=200)
def predict_anemia(input_data: AnemiaInput):
    try:
        result = anemiaPrediction(
            lemas=input_data.lemas,
            riwayat=input_data.riwayat,
            konjungtiva=input_data.konjungtiva,
            kuku=input_data.kuku
        )
        return result != "Tidak"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {e}")


@app.post("/stunting", status_code=200)
def predict_stunting(input_data: StuntingInput):
    try:
        return stuntingPrediction(
            usiaBulan=input_data.usiaBulan,
            tinggi=input_data.tinggi,
            kelamin=input_data.kelamin
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {e}")


@app.post("/zscore", status_code=200)
def predict_zscore(input_data: StuntingInput):
    try:
        return stuntingPrediction2(
            usiaBulan=input_data.usiaBulan,
            tinggi=input_data.tinggi,
            kelamin=input_data.kelamin
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {e}")


@app.post("/yolo", status_code=200)
async def predict_yolo(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        if not contents:
            raise ValueError("File upload kosong")

        image = Image.open(BytesIO(contents)).convert("RGB")
        img_np = np.array(image)

        # Jalankan prediksi YOLO tanpa menyimpan file
        results = model.predict(source=img_np, conf=0.4, save=False, verbose=False)

        predictions = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls.cpu().numpy()[0])
                conf = float(box.conf.cpu().numpy()[0])
                label = model.names[cls_id]
                bbox = box.xyxy.cpu().numpy()[0]
                predictions.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": [float(x) for x in bbox]
                })

        return {"predictions": predictions}

    except Exception as e:
        print("===== ERROR in /yolo =====")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"YOLO prediction error: {e}")

    finally:
        # Tutup file upload
        try:
            file.file.close()
        except:
            pass

        # Bersihkan file temporer YOLO
        for f in glob.glob("/tmp/Ultralytics/*"):
            try:
                os.remove(f)
            except:
                pass
