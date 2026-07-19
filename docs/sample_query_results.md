# Contoh Hasil Query Analitis

> Dokumen ini berisi cuplikan hasil nyata dari seluruh 15 query analitis pada `sql/03_analytical_queries.sql`, dijalankan terhadap database `data/esg_data_mart.db` hasil ETL. Digunakan sebagai bukti bahwa seluruh query berjalan valid dan sebagai referensi cepat tanpa perlu menjalankan ulang database.

> Dibuat otomatis dari hasil eksekusi aktual pada 2026-07-19.


## Q1. Peringkat 10 Perusahaan dengan Skor ESG Tertinggi (Tahun Terkini)

**Pertanyaan bisnis:** Siapa saja top performer ESG tahun evaluasi terbaru, dan di sektor/wilayah mana mereka?


| nama_perusahaan              | sektor                | wilayah_operasional   |   tahun_evaluasi |   total_skor_esg | peringkat_esg   |
|:-----------------------------|:----------------------|:----------------------|-----------------:|-----------------:|:----------------|
| PT Bumi Persada No. 2476     | Infrastruktur         | Kalimantan Timur      |             2026 |            97    | AAA             |
| PT Surya Makmur No. 729      | Teknologi & Informasi | Sulawesi Selatan      |             2026 |            96.33 | AAA             |
| PT Artha Lestari No. 186     | Kesehatan             | Sulawesi Selatan      |             2026 |            94.67 | AAA             |
| PT Nusantara Persada No. 981 | Teknologi & Informasi | Sumatera Utara        |             2026 |            94.67 | AAA             |
| PT Utama Sentosa No. 679     | Infrastruktur         | Kalimantan Timur      |             2026 |            94.67 | AAA             |
| PT Surya Lestari No. 425     | Energi & Pertambangan | Jawa Barat            |             2026 |            94.33 | AAA             |
| PT Indo Sejahtera No. 485    | Infrastruktur         | Kalimantan Timur      |             2026 |            94    | AAA             |
| PT Bina Karya No. 1400       | Energi & Pertambangan | Jawa Timur            |             2026 |            94    | AAA             |


*(menampilkan 8 dari 10 baris hasil)*


## Q2. Peringkat 10 Perusahaan dengan Skor ESG Terendah (Tahun Terkini)

**Pertanyaan bisnis:** Perusahaan mana yang berisiko tinggi dan perlu menjadi prioritas pendampingan kepatuhan?


| nama_perusahaan           | sektor                | wilayah_operasional   |   tahun_evaluasi |   total_skor_esg | peringkat_esg   |
|:--------------------------|:----------------------|:----------------------|-----------------:|-----------------:|:----------------|
| PT Citra Makmur No. 957   | Kesehatan             | Jawa Barat            |             2026 |            59.33 | BB              |
| PT Bina Energi No. 1048   | Kesehatan             | Jawa Barat            |             2026 |            59.67 | BB              |
| PT Citra Sentosa No. 705  | Keuangan              | Kalimantan Timur      |             2026 |            60.33 | BBB             |
| PT Bumi Lestari No. 1078  | Energi & Pertambangan | Kalimantan Timur      |             2026 |            60.33 | BBB             |
| PT Artha Makmur No. 1479  | Konsumer Primer       | Jawa Timur            |             2026 |            60.33 | BBB             |
| PT Sumber Jaya No. 1308   | Kesehatan             | Jawa Timur            |             2026 |            60.33 | BBB             |
| PT Bumi Sejahtera No. 750 | Infrastruktur         | Sumatera Utara        |             2026 |            61    | BBB             |
| PT Artha Abadi No. 1326   | Keuangan              | Jawa Timur            |             2026 |            61.33 | BBB             |


*(menampilkan 8 dari 10 baris hasil)*


## Q3. Rata-rata Skor ESG per Sektor per Tahun (Tren Multi-Tahun)

**Pertanyaan bisnis:** Bagaimana tren kinerja ESG tiap sektor industri dari tahun ke tahun? Sektor mana yang membaik atau memburuk?


| sektor                |   tahun_evaluasi |   jumlah_perusahaan_dinilai |   avg_skor_environmental |   avg_skor_social |   avg_skor_governance |   avg_total_skor_esg |
|:----------------------|-----------------:|----------------------------:|-------------------------:|------------------:|----------------------:|---------------------:|
| Energi & Pertambangan |             2022 |                          74 |                    73.12 |             76.8  |                 80.38 |                76.77 |
| Energi & Pertambangan |             2023 |                          79 |                    71.87 |             75.15 |                 77.63 |                74.89 |
| Energi & Pertambangan |             2024 |                          78 |                    73.36 |             76.92 |                 79.27 |                76.52 |
| Energi & Pertambangan |             2025 |                          86 |                    74.9  |             80.01 |                 77.53 |                77.48 |
| Energi & Pertambangan |             2026 |                          75 |                    76.65 |             77.13 |                 79.96 |                77.92 |
| Infrastruktur         |             2022 |                          92 |                    74.59 |             76.41 |                 80.39 |                77.13 |
| Infrastruktur         |             2023 |                          85 |                    75.41 |             76.92 |                 78.49 |                76.94 |
| Infrastruktur         |             2024 |                          79 |                    71.59 |             77.92 |                 80.65 |                76.72 |


*(menampilkan 8 dari 30 baris hasil)*


## Q4. Pertumbuhan Skor ESG Tahun-ke-Tahun (Year-over-Year) per Sektor

**Pertanyaan bisnis:** Berapa besar perubahan (%) rata-rata skor ESG tiap sektor dibanding tahun sebelumnya?


| sektor                |   tahun_evaluasi |   avg_total_skor_esg |   skor_tahun_sebelumnya |   selisih_poin_yoy |
|:----------------------|-----------------:|---------------------:|------------------------:|-------------------:|
| Energi & Pertambangan |             2022 |                76.77 |                  nan    |             nan    |
| Energi & Pertambangan |             2023 |                74.89 |                   76.77 |              -1.88 |
| Energi & Pertambangan |             2024 |                76.52 |                   74.89 |               1.63 |
| Energi & Pertambangan |             2025 |                77.48 |                   76.52 |               0.96 |
| Energi & Pertambangan |             2026 |                77.92 |                   77.48 |               0.44 |
| Infrastruktur         |             2022 |                77.13 |                  nan    |             nan    |
| Infrastruktur         |             2023 |                76.94 |                   77.13 |              -0.19 |
| Infrastruktur         |             2024 |                76.72 |                   76.94 |              -0.22 |


*(menampilkan 8 dari 30 baris hasil)*


## Q5. Distribusi Peringkat ESG per Sektor

**Pertanyaan bisnis:** Bagaimana komposisi peringkat (AAA/AA/A/BBB/BB) di masing-masing sektor?


| sektor                | peringkat_esg   |   jumlah_penilaian |   persentase_dalam_sektor |
|:----------------------|:----------------|-------------------:|--------------------------:|
| Energi & Pertambangan | AAA             |                 15 |                      3.83 |
| Energi & Pertambangan | AA              |                113 |                     28.83 |
| Energi & Pertambangan | A               |                195 |                     49.74 |
| Energi & Pertambangan | BBB             |                 69 |                     17.6  |
| Infrastruktur         | AAA             |                 18 |                      4.07 |
| Infrastruktur         | AA              |                146 |                     33.03 |
| Infrastruktur         | A               |                202 |                     45.7  |
| Infrastruktur         | BBB             |                 73 |                     16.52 |


*(menampilkan 8 dari 29 baris hasil)*


## Q6. Tingkat Kepatuhan Bulanan Keseluruhan (Semua Sektor)

**Pertanyaan bisnis:** Bulan apa saja yang tingkat kepatuhannya paling rendah dalam satu tahun berjalan? (musiman?)


|   bulan | nama_bulan   | kuartal   |   total_catatan |   jumlah_patuh |   persentase_patuh |
|--------:|:-------------|:----------|----------------:|---------------:|-------------------:|
|       1 | Januari      | Q1        |             201 |            125 |              62.19 |
|       2 | Februari     | Q1        |             186 |            105 |              56.45 |
|       3 | Maret        | Q1        |             192 |            133 |              69.27 |
|       4 | April        | Q2        |             214 |            141 |              65.89 |
|       5 | Mei          | Q2        |             203 |            134 |              66.01 |
|       6 | Juni         | Q2        |             227 |            143 |              63    |
|       7 | Juli         | Q3        |             218 |            137 |              62.84 |
|       8 | Agustus      | Q3        |             231 |            150 |              64.94 |


*(menampilkan 8 dari 12 baris hasil)*


## Q7. 10 Metrik ESG dengan Gap Kepatuhan Terbesar (Realisasi < Target)

**Pertanyaan bisnis:** Metrik ESG mana yang paling jauh dari target kepatuhan dan perlu perhatian program mitigasi?


| pilar         | nama_metrik                         |   target_kepatuhan_persen |   rata_rata_realisasi |   gap_terhadap_target |   jumlah_perlu_evaluasi |
|:--------------|:------------------------------------|--------------------------:|----------------------:|----------------------:|------------------------:|
| Social        | Hubungan Komunitas Lokal (Sub-2422) |                     99.88 |                 51.56 |                -48.32 |                       1 |
| Social        | Rasio Kesetaraan Gender (Sub-805)   |                     98.99 |                 51.37 |                -47.62 |                       1 |
| Environmental | Intensitas Karbon (Sub-1156)        |                     98.22 |                 50.9  |                -47.32 |                       1 |
| Environmental | Pengelolaan Limbah B3 (Sub-223)     |                     99.59 |                 52.51 |                -47.08 |                       1 |
| Environmental | Intensitas Karbon (Sub-446)         |                     98.79 |                 52.88 |                -45.91 |                       1 |
| Environmental | Konsumsi Air Bersih (Sub-1427)      |                     98.53 |                 53.3  |                -45.23 |                       1 |
| Social        | Tingkat Kecelakaan Kerja (Sub-691)  |                     96.48 |                 51.41 |                -45.07 |                       1 |
| Social        | Rasio Kesetaraan Gender (Sub-2448)  |                     96.6  |                 52.3  |                -44.3  |                       1 |


*(menampilkan 8 dari 10 baris hasil)*


## Q8. Total & Rata-rata Biaya Mitigasi per Pilar ESG dan Sektor

**Pertanyaan bisnis:** Pilar ESG (E/S/G) mana yang paling banyak menyerap biaya mitigasi di tiap sektor?


| sektor                | pilar         |   jumlah_aktivitas |   total_biaya_idr |   rata_rata_biaya_idr |
|:----------------------|:--------------|-------------------:|------------------:|----------------------:|
| Energi & Pertambangan | Environmental |                152 |    39,376,883,191 |           259,058,442 |
| Energi & Pertambangan | Social        |                130 |    35,795,684,977 |           275,351,423 |
| Energi & Pertambangan | Governance    |                118 |    31,469,819,725 |           266,693,388 |
| Infrastruktur         | Social        |                144 |    36,174,539,439 |           251,212,079 |
| Infrastruktur         | Environmental |                124 |    32,997,531,473 |           266,109,125 |
| Infrastruktur         | Governance    |                120 |    30,778,843,011 |           256,490,358 |
| Kesehatan             | Social        |                164 |    40,852,072,662 |           249,098,004 |
| Kesehatan             | Environmental |                144 |    38,047,692,054 |           264,220,084 |


*(menampilkan 8 dari 18 baris hasil)*


## Q9. Peringkat Wilayah Operasional Berdasarkan Rata-rata Skor ESG

**Pertanyaan bisnis:** Wilayah mana yang secara rata-rata memiliki kinerja ESG terbaik / perlu perhatian khusus?


| wilayah_operasional   |   jumlah_perusahaan |   rata_rata_skor_esg |   skor_minimum |   skor_maksimum |
|:----------------------|--------------------:|---------------------:|---------------:|----------------:|
| Sulawesi Selatan      |                 253 |                77.59 |          55.67 |           98    |
| Jawa Barat            |                 294 |                77.42 |          57.33 |           95.33 |
| Sumatera Utara        |                 235 |                77.1  |          56.33 |           97.67 |
| DKI Jakarta           |                 269 |                77    |          56.67 |           96.67 |
| Jawa Timur            |                 270 |                76.61 |          58.33 |           97    |
| Kalimantan Timur      |                 248 |                76.31 |          60    |           97    |


## Q10. Korelasi Sederhana: Lama Perusahaan Terdaftar (Listing) vs Skor ESG

**Pertanyaan bisnis:** Apakah perusahaan yang lebih lama listing di bursa cenderung memiliki tata kelola ESG yang lebih matang?


| kelompok_tahun_listing   |   jumlah_perusahaan |   rata_rata_skor_esg |
|:-------------------------|--------------------:|---------------------:|
| 2010-2012                |                 320 |                77.19 |
| 2013-2015                |                 312 |                76.64 |
| 2016-2018                |                 299 |                76.94 |
| 2019-2021                |                 324 |                77.01 |
| 2022-2024                |                 314 |                77.25 |


## Q11. Perusahaan dengan Status "Perlu Evaluasi" Terbanyak

**Pertanyaan bisnis:** Perusahaan mana yang paling sering gagal mencapai target kepatuhan pada aktivitas bulanannya? (kandidat audit prioritas)


| nama_perusahaan             | sektor                |   total_catatan_aktivitas |   jumlah_perlu_evaluasi |   persentase_perlu_evaluasi |
|:----------------------------|:----------------------|--------------------------:|------------------------:|----------------------------:|
| PT Bina Sentosa No. 280     | Teknologi & Informasi |                         3 |                       3 |                         100 |
| PT Nusantara Karya No. 388  | Kesehatan             |                         3 |                       3 |                         100 |
| PT Bina Sejahtera No. 561   | Infrastruktur         |                         3 |                       3 |                         100 |
| PT Sumber Persada No. 826   | Energi & Pertambangan |                         3 |                       3 |                         100 |
| PT Bina Energi No. 1122     | Keuangan              |                         3 |                       3 |                         100 |
| PT Utama Sejahtera No. 1351 | Konsumer Primer       |                         3 |                       3 |                         100 |
| PT Sumber Tbk No. 2087      | Konsumer Primer       |                         3 |                       3 |                         100 |
| PT Nusantara Abadi No. 246  | Energi & Pertambangan |                         4 |                       3 |                          75 |


*(menampilkan 8 dari 15 baris hasil)*


## Q12. Perusahaan "Konsisten Unggul": Selalu Peringkat AAA/AA

**Pertanyaan bisnis:** Perusahaan mana yang layak dijadikan studi kasus/benchmark ESG karena konsisten unggul di setiap tahun evaluasi yang dimilikinya?


| nama_perusahaan             | sektor                |   jumlah_tahun_dinilai |   skor_terendah_tercatat | daftar_peringkat   |
|:----------------------------|:----------------------|-----------------------:|-------------------------:|:-------------------|
| PT Artha Sejahtera No. 1794 | Energi & Pertambangan |                      2 |                    92.33 | AAA                |
| PT Mega Persada No. 194     | Konsumer Primer       |                      2 |                    91.67 | AAA                |
| PT Sumber Persada No. 757   | Energi & Pertambangan |                      2 |                    90.67 | AAA                |
| PT Indo Lestari No. 2440    | Infrastruktur         |                      2 |                    88.33 | AA                 |
| PT Artha Sejahtera No. 1516 | Teknologi & Informasi |                      2 |                    88    | AA,AAA             |
| PT Bina Lestari No. 1681    | Konsumer Primer       |                      2 |                    87.33 | AA,AAA             |
| PT Surya Makmur No. 1335    | Teknologi & Informasi |                      2 |                    86    | AA                 |
| PT Bumi Energi No. 1275     | Energi & Pertambangan |                      2 |                    85.67 | AA                 |


*(menampilkan 8 dari 15 baris hasil)*


## Q13. Ringkasan Eksekutif (Executive Summary) - Satu Baris KPI Utama

**Pertanyaan bisnis:** Berikan ringkasan angka-angka kunci data mart ini untuk slide pembuka laporan manajemen.


|   total_perusahaan |   total_sektor |   total_wilayah |   total_penilaian_tahunan |   rata_rata_skor_esg_keseluruhan |   total_catatan_aktivitas |   persentase_kepatuhan_keseluruhan |   total_biaya_mitigasi_idr |
|-------------------:|---------------:|----------------:|--------------------------:|---------------------------------:|--------------------------:|-----------------------------------:|---------------------------:|
|               2500 |              6 |               6 |                      2500 |                               77 |                      2500 |                               63.8 |            637,612,549,715 |


## Q14. Efisiensi Biaya Mitigasi: Biaya per Poin Realisasi

**Pertanyaan bisnis:** Sektor mana yang paling efisien secara biaya dalam mencapai realisasi metrik ESG-nya?


| sektor                |   rata_rata_realisasi |   total_biaya_idr |   biaya_per_poin_realisasi_idr |
|:----------------------|----------------------:|------------------:|-------------------------------:|
| Teknologi & Informasi |                 86.36 |    92,776,382,255 |                  1,074,331,277 |
| Infrastruktur         |                 84.57 |    99,950,913,923 |                  1,181,826,245 |
| Konsumer Primer       |                 83.49 |   102,985,350,490 |                  1,233,503,792 |
| Energi & Pertambangan |                 84.83 |   106,642,387,893 |                  1,257,197,651 |
| Kesehatan             |                 84.77 |   115,515,552,836 |                  1,362,680,576 |
| Keuangan              |                 84.66 |   119,741,962,318 |                  1,414,379,144 |


## Q15. Ringkasan Kepatuhan per Pilar ESG (Environmental/Social/Governance)

**Pertanyaan bisnis:** Dari tiga pilar ESG, mana yang tingkat kepatuhannya paling rendah secara keseluruhan?


| pilar         |   total_catatan |   jumlah_patuh |   persentase_patuh |   rata_rata_realisasi |
|:--------------|----------------:|---------------:|-------------------:|----------------------:|
| Environmental |             851 |            532 |              62.51 |                 84.97 |
| Social        |             888 |            563 |              63.4  |                 84.38 |
| Governance    |             761 |            500 |              65.7  |                 84.93 |
