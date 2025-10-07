def calculate_dds(detected_labels: list) -> int:
    dds_categories = [
        "makanan_berpati",
        "daging",
        "telur",
        "produk_susu",
        "kacang_legume",
        "buah_sayur_vitA",
        "buah_sayur_lainnya"
    ]
    return len(set(item for item in detected_labels if item in dds_categories))
