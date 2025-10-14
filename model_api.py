from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import pandas as pd
import os
from ultralytics import YOLO
import shutil
import uuid
import cv2
from PIL import Image
# Import fungsi-fungsi yang Anda berikan
# Pastikan file-file ini ada di direktori yang sama
from anemia import deteksi_anemia
# from ultralytics import YOLO
# from dds import calculate_dds
# from hitung_tb_u import hitung_z_score_tb_u
# from ekonomi import klasifikasi_ekonomi
# from rekomendasi import generate_rekomendasi
# from sanitasi import deteksi_sanitasi

# Path ke file antropometri
DATA_PATH = "antropometri_tb_u.csv"

# Inisialisasi aplikasi FastAPI
app = FastAPI()

# --- Definisi Model Pydantic untuk Request Body ---

model = YOLO("best.pt")


class AnemiaInput(BaseModel):
    """
    Model untuk data input fungsi anemiaPrediction.
    FastAPI akan secara otomatis memvalidasi data JSON
    dari request body sesuai dengan model ini.
    """
    lemas: bool
    riwayat: bool
    konjungtiva: bool
    kuku: bool

class StuntingInput(BaseModel):
    """
    Model untuk data input fungsi stuntingPrediction.
    """
    usiaBulan: int
    tinggi: int
    kelamin: str

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


# --- Fungsi Prediksi Anemia ---

def anemiaPrediction(lemas: bool, riwayat: bool, konjungtiva: bool, kuku: bool):
    """
    Fungsi untuk mendeteksi status anemia.
    """
    # Menggunakan fungsi deteksi_anemia dari file anemia.py
    status_anemia = deteksi_anemia(lemas=lemas, riwayat=riwayat, konjungtiva_pucat=konjungtiva, kuku_pucat=kuku)
    print(f"Hasil prediksi anemia: {status_anemia}")
    return status_anemia

# --- Fungsi Prediksi Stunting ---

def stuntingPrediction(usiaBulan: int, tinggi: int, kelamin: str):
    """
    Fungsi untuk memprediksi status stunting.
    """
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

def stuntingPrediction2(usiaBulan: int, tinggi: int, kelamin: str):
    """
    Fungsi untuk memprediksi status stunting.
    """
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

    print(z_score)

    return z_score 

# -------------------------------------------------------------

@app.post("/anemia", status_code=200)
def predict_anemia(input_data: AnemiaInput):
    """
    Menerima data gejala anemia dari request body dan mengembalikan prediksi.
    """
    try:
        result = anemiaPrediction(
            lemas=input_data.lemas,
            riwayat=input_data.riwayat,
            konjungtiva=input_data.konjungtiva,
            kuku=input_data.kuku
        )
        if(result == "Tidak"):
            endResult = False
        else:
            endResult = True

        return endResult
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {e}")

@app.post("/stunting", status_code=200)
def predict_stunting(input_data: StuntingInput):
    """
    Menerima data antropometri dari request body dan mengembalikan prediksi stunting.
    """
    try:
        result = stuntingPrediction(
            usiaBulan=input_data.usiaBulan,
            tinggi=input_data.tinggi,
            kelamin=input_data.kelamin
        )
        return result
    except HTTPException as he:
        # Menangani HTTPException yang dilempar dari fungsi stuntingPrediction
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {e}") 
    
@app.post("/zscore", status_code=200)
def predict_stunting(input_data: StuntingInput):
    """
    Menerima data antropometri dari request body dan mengembalikan prediksi stunting.
    """
    try:
        result = stuntingPrediction2(
            usiaBulan=input_data.usiaBulan,
            tinggi=input_data.tinggi,
            kelamin=input_data.kelamin
        )
        print(result)
        return result
    except HTTPException as he:
        # Menangani HTTPException yang dilempar dari fungsi stuntingPrediction
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {e}") 
    
    
@app.post("/yolo", status_code=200)
async def predict_yolo(file: UploadFile = File(...)):
    """
    Menerima file gambar, menjalankan YOLO, menyimpan hasil bounding box,
    dan mengembalikan hasil prediksi.
    """
    try:
        # Simpan file upload ke sementara
        temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Jalankan prediksi YOLO
        results = model.predict(source=temp_filename, conf=0.4, save=False)

        predictions = []
        output_files = []

        # Loop hasil prediksi
        for idx, r in enumerate(results):
            # Ambil box, label, confidence
            for box in r.boxes:
                cls_id = int(box.cls.cpu().numpy()[0])
                conf = float(box.conf.cpu().numpy()[0])
                label = model.names[cls_id]
                predictions.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": box.xyxy.cpu().numpy()[0].tolist()
                })

            # Simpan gambar dengan bounding box
            # im_array = r.plot()  # numpy array dengan bbox
            # im_rgb = cv2.cvtColor(im_array, cv2.COLOR_BGR2RGB)  # convert ke RGB
            # output_path = f"output_{uuid.uuid4().hex}.jpg"
            # Image.fromarray(im_rgb).save(output_path)
            # output_files.append(output_path)

        # Hapus file input
        os.remove(temp_filename)

        return {
            "predictions": predictions,
            "output_files": output_files  # list file hasil bbox
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YOLO prediction error: {e}")
