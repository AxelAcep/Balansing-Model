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
