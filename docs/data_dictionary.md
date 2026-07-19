# Data Dictionary — ESG Data Mart

Dokumen ini mendefinisikan setiap tabel dan kolom yang ada di dalam data mart, termasuk asal data (sumber CSV mentah vs. dibangun oleh ETL), tipe data, dan aturan bisnis/constraint yang berlaku. Gunakan dokumen ini sebagai referensi utama saat menulis query baru.

---

## 1. Ringkasan Tabel

| Tabel                       | Jenis           | Grain (1 baris =)                                  | Jumlah Baris | Sumber                        |
|------------------------------|-----------------|-----------------------------------------------------|-------------:|--------------------------------|
| `dim_perusahaan`              | Dimensi          | 1 perusahaan                                         | 2.500        | `dim_perusahaan.csv`           |
| `dim_metrik_esg`               | Dimensi          | 1 metrik ESG                                         | 2.500        | `dim_metrik_esg.csv`           |
| `dim_waktu_bulan`              | Dimensi turunan  | 1 bulan kalender (1–12)                              | 12           | dibangun oleh ETL              |
| `dim_peringkat_esg`            | Dimensi referensi| 1 kategori peringkat ESG                             | 5            | dibangun oleh ETL              |
| `fact_penilaian_tahunan`       | Fakta            | 1 perusahaan × 1 tahun evaluasi                      | 2.500        | `fact_penilaian_tahunan.csv`   |
| `fact_catatan_aktivitas`        | Fakta            | 1 perusahaan × 1 metrik × 1 bulan                     | 2.500        | `fact_catatan_aktivitas.csv`   |

---

## 2. Dimensi

### 2.1 `dim_perusahaan`
Profil induk (master data) setiap perusahaan yang dinilai dalam program ESG.

| Kolom                  | Tipe    | Deskripsi                                                                 | Contoh Nilai              |
|-------------------------|---------|-----------------------------------------------------------------------------|-----------------------------|
| `company_id` **(PK)**   | TEXT    | Kode unik perusahaan                                                        | `COMP-0001`                 |
| `nama_perusahaan`       | TEXT    | Nama resmi perusahaan                                                       | `PT Utama Sentosa No. 1`    |
| `sektor`                | TEXT    | Sektor industri. 6 nilai unik: Kesehatan, Konsumer Primer, Teknologi & Informasi, Infrastruktur, Keuangan, Energi & Pertambangan | `Kesehatan` |
| `wilayah_operasional`   | TEXT    | Wilayah operasional utama. 6 nilai unik: Sumatera Utara, DKI Jakarta, Sulawesi Selatan, Kalimantan Timur, Jawa Timur, Jawa Barat | `DKI Jakarta` |
| `tahun_listing`         | INTEGER | Tahun perusahaan pertama kali listing/tercatat                              | `2010`–`2024`               |

### 2.2 `dim_metrik_esg`
Katalog metrik ESG yang diukur pada setiap catatan aktivitas.

| Kolom                        | Tipe  | Deskripsi                                                              | Contoh Nilai                     |
|--------------------------------|-------|---------------------------------------------------------------------------|-------------------------------------|
| `metric_id` **(PK)**           | TEXT  | Kode unik metrik                                                          | `METRIC-0001`                       |
| `pilar`                        | TEXT  | Pilar ESG. Nilai: `Environmental`, `Social`, `Governance`                 | `Social`                            |
| `nama_metrik`                  | TEXT  | Nama metrik yang diukur                                                   | `Pelatihan Karyawan (Jam) (Sub-1)`  |
| `satuan`                       | TEXT  | Satuan pengukuran (deskriptif, dapat berupa gabungan beberapa satuan)     | `Persentase / Jam / Tingkat Kasus`  |
| `target_kepatuhan_persen`      | REAL  | Target kepatuhan yang ditetapkan untuk metrik ini (skala 0–100)          | `92.14`                             |

### 2.3 `dim_waktu_bulan` *(dimensi turunan)*
Dibangun oleh ETL sebagai kalender bulan statis (1–12), digunakan untuk pelaporan pola musiman pada `fact_catatan_aktivitas`.

| Kolom                 | Tipe    | Deskripsi                              |
|-------------------------|---------|-------------------------------------------|
| `bulan` **(PK)**         | INTEGER | Nomor bulan (1 = Januari … 12 = Desember) |
| `nama_bulan`             | TEXT    | Nama bulan lengkap (Bahasa Indonesia)     |
| `nama_bulan_singkat`     | TEXT    | Singkatan 3 huruf                        |
| `kuartal`                | TEXT    | Q1–Q4                                     |
| `semester`               | TEXT    | Semester 1 / Semester 2                   |

> **Catatan penting:** `fact_catatan_aktivitas.csv` sumber hanya menyimpan nomor bulan (1–12) **tanpa informasi tahun**. Oleh karena itu, dimensi ini hanya merepresentasikan bulan kalender generik, bukan bulan-tahun spesifik. Lihat bagian "Asumsi & Keterbatasan Data" di `README.md` untuk detail dan implikasinya terhadap analisis.

### 2.4 `dim_peringkat_esg` *(dimensi referensi)*
Dibangun oleh ETL untuk memberi urutan & kategori risiko pada nilai `peringkat_esg` yang muncul di `fact_penilaian_tahunan`, agar dapat diurutkan (sort) dan dikelompokkan secara benar dalam laporan (bukan diurutkan secara alfabet).

| Kolom                  | Tipe    | Deskripsi                                                        |
|--------------------------|---------|----------------------------------------------------------------------|
| `peringkat_esg` **(PK)** | TEXT    | Kode peringkat: `AAA`, `AA`, `A`, `BBB`, `BB`                        |
| `urutan_peringkat`       | INTEGER | 1 = terbaik (AAA) … 5 = terendah (BB)                                |
| `kategori_risiko`        | TEXT    | Rendah / Sedang / Tinggi                                              |
| `deskripsi`              | TEXT    | Deskripsi naratif singkat tiap peringkat                             |

Pemetaan skor → peringkat (berdasarkan observasi data aktual):

| Peringkat | Rentang `total_skor_esg` |
|-----------|----------------------------|
| AAA       | 90.00 – 98.00               |
| AA        | 80.00 – 89.67                |
| A         | 70.00 – 79.67                |
| BBB       | 60.00 – 69.67                |
| BB        | 55.67 – 59.67                |

---

## 3. Fakta

### 3.1 `fact_penilaian_tahunan`
Hasil penilaian ESG tahunan tiap perusahaan oleh lembaga penilai.

| Kolom                    | Tipe    | Deskripsi                                                        | Constraint                  |
|----------------------------|---------|----------------------------------------------------------------------|--------------------------------|
| `fact_score_id` **(PK)**   | TEXT    | Kode unik baris penilaian                                            | Unique                       |
| `company_id` **(FK)**      | TEXT    | Referensi ke `dim_perusahaan`                                        | -                             |
| `tahun_evaluasi`           | INTEGER | Tahun evaluasi (degenerate dimension). Rentang aktual: 2022–2026     | -                             |
| `skor_environmental`       | INTEGER | Skor pilar Environmental (0–100)                                     | 0 ≤ x ≤ 100                    |
| `skor_social`               | INTEGER | Skor pilar Social (0–100)                                            | 0 ≤ x ≤ 100                    |
| `skor_governance`           | INTEGER | Skor pilar Governance (0–100)                                        | 0 ≤ x ≤ 100                    |
| `total_skor_esg`            | REAL    | Rata-rata dari 3 skor pilar di atas                                   | = AVG(E, S, G), divalidasi ETL |
| `peringkat_esg` **(FK)**    | TEXT    | Referensi ke `dim_peringkat_esg`                                      | -                             |

**Catatan grain**: satu perusahaan dapat memiliki lebih dari satu baris jika dinilai pada tahun yang berbeda (245 dari 2.500 `company_id` muncul lebih dari satu kali). Perusahaan **tidak dijamin** dinilai setiap tahun secara berturut-turut.

### 3.2 `fact_catatan_aktivitas`
Catatan realisasi bulanan tiap metrik ESG per perusahaan, termasuk biaya mitigasi kepatuhan.

| Kolom                     | Tipe    | Deskripsi                                                       | Constraint                                |
|------------------------------|---------|----------------------------------------------------------------------|-----------------------------------------------|
| `fact_activity_id` **(PK)**  | TEXT    | Kode unik baris aktivitas                                            | Unique                                       |
| `company_id` **(FK)**        | TEXT    | Referensi ke `dim_perusahaan`                                        | -                                             |
| `metric_id` **(FK)**         | TEXT    | Referensi ke `dim_metrik_esg`                                        | -                                             |
| `bulan` **(FK)**              | INTEGER | Referensi ke `dim_waktu_bulan` (1–12, tanpa tahun — lihat catatan)   | 1 ≤ x ≤ 12                                    |
| `nilai_realisasi`             | REAL    | Nilai realisasi aktual metrik pada bulan tsb.                        | Rentang aktual data: 50.01–119.99             |
| `status_kepatuhan`             | TEXT    | Status kepatuhan hasil evaluasi                                       | `Patuh` atau `Perlu Evaluasi`                 |
| `biaya_mitigasi_idr`           | INTEGER | Biaya mitigasi yang dikeluarkan (Rupiah)                              | ≥ 0. Rentang aktual: Rp15.023.802 – Rp498.912.612 |

> `nilai_realisasi` dapat melebihi 100 (maksimum aktual data ≈ 119,99) karena beberapa metrik ESG diukur dalam satuan non-persentase (mis. jam pelatihan, ton CO2e) sehingga `nilai_realisasi` bukan selalu representasi persentase langsung terhadap `target_kepatuhan_persen`. Perbandingan langsung keduanya (seperti pada `v_gap_kepatuhan_metrik`) sebaiknya dibaca sebagai indikator arah (gap positif/negatif), bukan selisih persentase presisi tinggi untuk metrik dengan satuan non-persentase.

---

## 4. Reporting Views (lapisan semantik)

| View                              | Deskripsi Singkat                                                                 |
|-------------------------------------|----------------------------------------------------------------------------------|
| `v_ringkasan_skor_perusahaan`       | Gabungan penilaian tahunan + profil perusahaan + atribut peringkat                |
| `v_kepatuhan_bulanan_sektor`         | Ringkasan tingkat kepatuhan & biaya mitigasi per sektor per bulan                  |
| `v_tren_skor_tahunan_sektor`         | Rata-rata skor ESG per sektor per tahun evaluasi                                  |
| `v_gap_kepatuhan_metrik`             | Perbandingan rata-rata realisasi tiap metrik terhadap target kepatuhannya          |
| `v_biaya_mitigasi_pilar`             | Total & rata-rata biaya mitigasi per pilar ESG dan sektor                          |

Definisi lengkap ada di `sql/02_create_views.sql`.

---

## 5. Diagram Relasi

Lihat `docs/erd_diagram.png` untuk diagram ERD visual, atau `sql/01_create_schema.sql` untuk definisi DDL lengkap.

```
dim_perusahaan ──┬──< fact_penilaian_tahunan >── dim_peringkat_esg
                  │
                  └──< fact_catatan_aktivitas >── dim_metrik_esg
                                    │
                                    └──< dim_waktu_bulan
```
