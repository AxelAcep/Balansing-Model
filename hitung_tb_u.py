import pandas as pd
import os

# Path ke file antropometri
DATA_PATH = "data/antropometri_tb_u.csv"

def hitung_z_score_tb_u(usia_bulan, tinggi_cm, jenis_kelamin):
    """
    Menghitung Z-score TB/U berdasarkan standar PMK.

    Params:
        usia_bulan (int): usia anak dalam bulan
        tinggi_cm (float): tinggi badan anak
        jenis_kelamin (str): 'L' atau 'P'

    Returns:
        tuple: (z_score, status)
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data PMK tidak ditemukan di: {DATA_PATH}")
    
    df = pd.read_csv(DATA_PATH)

    # Filter berdasarkan usia & jenis kelamin
    baris = df[
        (df["usia_bulan"] == usia_bulan) &
        (df["jenis_kelamin"].str.upper() == jenis_kelamin.upper())
    ]

    if baris.empty:
        raise ValueError(f"Tidak ditemukan data PMK untuk usia {usia_bulan} bulan dan jenis kelamin {jenis_kelamin}")

    # Ambil nilai median dan -1 SD untuk hitung SD
    median = float(baris["median"].values[0])
    minus_1sd = float(baris["minus_1sd"].values[0])


    # SD didefinisikan sebagai selisih median dan -1SD
    sd = median - minus_1sd

    # Hitung z-score
    z_score = (tinggi_cm - median) / sd

    # Klasifikasi status TB/U
    if z_score < -3:
        status = "Sangat Pendek"
    elif -3 <= z_score < -2:
        status = "Pendek"
    elif -2 <= z_score <= 3:
        status = "Normal"
    else:
        status = "Tinggi"

    return z_score, status
if __name__ == "__main__":
    # Contoh tes lokal
    usia_bulan = 24
    tinggi = 79.0
    jk = 'L'

    z, status = hitung_z_score_tb_u(usia_bulan, tinggi, jk)
    print(f"Z-score: {z:.2f}, Status: {status}")