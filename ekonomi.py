def klasifikasi_ekonomi(pengeluaran: int) -> str:
    if pengeluaran < 582932:
        return "Kelas Bawah"
    elif pengeluaran < 874398:
        return "Rentan Kelas Bawah"
    elif pengeluaran < 2040262:
        return "Menuju Kelas Menengah"
    elif pengeluaran < 9909844:
        return "Kelas Menengah"
    else:
        return "Kelas Atas"
