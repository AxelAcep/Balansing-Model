def deteksi_anemia(lemas: bool, riwayat: bool, konjungtiva_pucat: bool, kuku_pucat: bool) -> str:
    indikator = [
        lemas,
        riwayat,
        konjungtiva_pucat,
        kuku_pucat
    ]
    # Jika 2 atau lebih indikator bernilai True → kemungkinan anemia
    if indikator.count(True) >= 2:
        return "Ya"
    return "Tidak"