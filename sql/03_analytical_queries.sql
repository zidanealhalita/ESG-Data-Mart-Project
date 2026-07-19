-- =====================================================================
-- ESG DATA MART - ANALYTICAL / BUSINESS REPORTING QUERIES
-- =====================================================================
-- Penulis  : Muhammad Zidane Alhalita
-- Deskripsi:
--   Kumpulan query analitis yang mensimulasikan permintaan laporan
--   nyata dari pemangku kepentingan (manajemen, tim kepatuhan/
--   sustainability, investor relations). Setiap query diberi nomor,
--   judul, pertanyaan bisnis yang dijawab, dan penjelasan singkat.
--
--   Query ini dapat dijalankan langsung setelah 01_create_schema.sql,
--   02_create_views.sql, dan proses ETL selesai dijalankan.
--
--   Cara menjalankan (CLI):
--     sqlite3 data/esg_data_mart.db < sql/03_analytical_queries.sql
-- =====================================================================


-- =====================================================================
-- Q1. Peringkat 10 Perusahaan dengan Skor ESG Tertinggi (Tahun Terkini)
-- Pertanyaan bisnis : "Siapa saja top performer ESG tahun evaluasi
--                       terbaru, dan di sektor/wilayah mana mereka?"
-- =====================================================================
SELECT
    nama_perusahaan,
    sektor,
    wilayah_operasional,
    tahun_evaluasi,
    total_skor_esg,
    peringkat_esg
FROM v_ringkasan_skor_perusahaan
WHERE tahun_evaluasi = (SELECT MAX(tahun_evaluasi) FROM fact_penilaian_tahunan)
ORDER BY total_skor_esg DESC
LIMIT 10;


-- =====================================================================
-- Q2. Peringkat 10 Perusahaan dengan Skor ESG Terendah (Tahun Terkini)
-- Pertanyaan bisnis : "Perusahaan mana yang berisiko tinggi dan perlu
--                       menjadi prioritas pendampingan kepatuhan?"
-- =====================================================================
SELECT
    nama_perusahaan,
    sektor,
    wilayah_operasional,
    tahun_evaluasi,
    total_skor_esg,
    peringkat_esg
FROM v_ringkasan_skor_perusahaan
WHERE tahun_evaluasi = (SELECT MAX(tahun_evaluasi) FROM fact_penilaian_tahunan)
ORDER BY total_skor_esg ASC
LIMIT 10;


-- =====================================================================
-- Q3. Rata-rata Skor ESG per Sektor per Tahun (Tren Multi-Tahun)
-- Pertanyaan bisnis : "Bagaimana tren kinerja ESG tiap sektor industri
--                       dari tahun ke tahun? Sektor mana yang membaik
--                       atau memburuk?"
-- =====================================================================
SELECT
    sektor,
    tahun_evaluasi,
    jumlah_perusahaan_dinilai,
    avg_skor_environmental,
    avg_skor_social,
    avg_skor_governance,
    avg_total_skor_esg
FROM v_tren_skor_tahunan_sektor
ORDER BY sektor, tahun_evaluasi;


-- =====================================================================
-- Q4. Pertumbuhan Skor ESG Tahun-ke-Tahun (Year-over-Year) per Sektor
-- Pertanyaan bisnis : "Berapa besar perubahan (%) rata-rata skor ESG
--                       tiap sektor dibanding tahun sebelumnya?"
-- Teknik            : window function LAG() untuk membandingkan baris
--                       tahun berjalan dengan tahun sebelumnya.
-- =====================================================================
SELECT
    sektor,
    tahun_evaluasi,
    avg_total_skor_esg,
    LAG(avg_total_skor_esg) OVER (PARTITION BY sektor ORDER BY tahun_evaluasi)
        AS skor_tahun_sebelumnya,
    ROUND(
        avg_total_skor_esg
        - LAG(avg_total_skor_esg) OVER (PARTITION BY sektor ORDER BY tahun_evaluasi)
    , 2) AS selisih_poin_yoy
FROM v_tren_skor_tahunan_sektor
ORDER BY sektor, tahun_evaluasi;


-- =====================================================================
-- Q5. Distribusi Peringkat ESG per Sektor
-- Pertanyaan bisnis : "Bagaimana komposisi peringkat (AAA/AA/A/BBB/BB)
--                       di masing-masing sektor?"
-- =====================================================================
SELECT
    sektor,
    peringkat_esg,
    COUNT(*) AS jumlah_penilaian,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY sektor), 2)
        AS persentase_dalam_sektor
FROM v_ringkasan_skor_perusahaan
GROUP BY sektor, peringkat_esg
ORDER BY sektor,
         MIN(urutan_peringkat);


-- =====================================================================
-- Q6. Tingkat Kepatuhan Bulanan Keseluruhan (Semua Sektor)
-- Pertanyaan bisnis : "Bulan apa saja yang tingkat kepatuhannya paling
--                       rendah dalam satu tahun berjalan? (musiman?)"
-- =====================================================================
SELECT
    w.bulan,
    w.nama_bulan,
    w.kuartal,
    COUNT(*)                                                      AS total_catatan,
    SUM(CASE WHEN a.status_kepatuhan = 'Patuh' THEN 1 ELSE 0 END) AS jumlah_patuh,
    ROUND(100.0 * SUM(CASE WHEN a.status_kepatuhan = 'Patuh' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                         AS persentase_patuh
FROM fact_catatan_aktivitas a
JOIN dim_waktu_bulan w ON a.bulan = w.bulan
GROUP BY w.bulan, w.nama_bulan, w.kuartal
ORDER BY w.bulan;


-- =====================================================================
-- Q7. 10 Metrik ESG dengan Gap Kepatuhan Terbesar (Realisasi < Target)
-- Pertanyaan bisnis : "Metrik ESG mana yang paling jauh dari target
--                       kepatuhan dan perlu perhatian program mitigasi?"
-- =====================================================================
SELECT
    pilar,
    nama_metrik,
    target_kepatuhan_persen,
    rata_rata_realisasi,
    gap_terhadap_target,
    jumlah_perlu_evaluasi
FROM v_gap_kepatuhan_metrik
WHERE gap_terhadap_target < 0
ORDER BY gap_terhadap_target ASC
LIMIT 10;


-- =====================================================================
-- Q8. Total & Rata-rata Biaya Mitigasi per Pilar ESG dan Sektor
-- Pertanyaan bisnis : "Pilar ESG (E/S/G) mana yang paling banyak
--                       menyerap biaya mitigasi di tiap sektor?"
-- =====================================================================
SELECT
    sektor,
    pilar,
    jumlah_aktivitas,
    total_biaya_idr,
    rata_rata_biaya_idr
FROM v_biaya_mitigasi_pilar
ORDER BY sektor, total_biaya_idr DESC;


-- =====================================================================
-- Q9. Peringkat Wilayah Operasional Berdasarkan Rata-rata Skor ESG
-- Pertanyaan bisnis : "Wilayah mana yang secara rata-rata memiliki
--                       kinerja ESG terbaik / perlu perhatian khusus?"
-- =====================================================================
SELECT
    wilayah_operasional,
    COUNT(DISTINCT company_id)       AS jumlah_perusahaan,
    ROUND(AVG(total_skor_esg), 2)    AS rata_rata_skor_esg,
    ROUND(MIN(total_skor_esg), 2)    AS skor_minimum,
    ROUND(MAX(total_skor_esg), 2)    AS skor_maksimum
FROM v_ringkasan_skor_perusahaan
GROUP BY wilayah_operasional
ORDER BY rata_rata_skor_esg DESC;


-- =====================================================================
-- Q10. Korelasi Sederhana: Lama Perusahaan Terdaftar (Listing) vs Skor ESG
-- Pertanyaan bisnis : "Apakah perusahaan yang lebih lama listing di
--                       bursa cenderung memiliki tata kelola ESG yang
--                       lebih matang?"
-- Catatan           : dikelompokkan per dekade listing agar mudah dibaca.
-- =====================================================================
SELECT
    CASE
        WHEN tahun_listing < 2013 THEN '2010-2012'
        WHEN tahun_listing < 2016 THEN '2013-2015'
        WHEN tahun_listing < 2019 THEN '2016-2018'
        WHEN tahun_listing < 2022 THEN '2019-2021'
        ELSE '2022-2024'
    END                                AS kelompok_tahun_listing,
    COUNT(DISTINCT company_id)         AS jumlah_perusahaan,
    ROUND(AVG(total_skor_esg), 2)      AS rata_rata_skor_esg
FROM v_ringkasan_skor_perusahaan
GROUP BY kelompok_tahun_listing
ORDER BY kelompok_tahun_listing;


-- =====================================================================
-- Q11. Perusahaan dengan Status "Perlu Evaluasi" Terbanyak
-- Pertanyaan bisnis : "Perusahaan mana yang paling sering gagal
--                       mencapai target kepatuhan pada aktivitas
--                       bulanannya? (kandidat audit prioritas)"
-- =====================================================================
SELECT
    p.nama_perusahaan,
    p.sektor,
    COUNT(*)                                                            AS total_catatan_aktivitas,
    SUM(CASE WHEN a.status_kepatuhan = 'Perlu Evaluasi' THEN 1 ELSE 0 END)
        AS jumlah_perlu_evaluasi,
    ROUND(100.0 * SUM(CASE WHEN a.status_kepatuhan = 'Perlu Evaluasi' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                                AS persentase_perlu_evaluasi
FROM fact_catatan_aktivitas a
JOIN dim_perusahaan p ON a.company_id = p.company_id
GROUP BY p.company_id, p.nama_perusahaan, p.sektor
HAVING COUNT(*) >= 3                       -- hanya perusahaan dengan cukup data
ORDER BY persentase_perlu_evaluasi DESC, jumlah_perlu_evaluasi DESC
LIMIT 15;


-- =====================================================================
-- Q12. Perusahaan "Konsisten Unggul": Selalu Peringkat AAA/AA
-- Pertanyaan bisnis : "Perusahaan mana yang layak dijadikan studi
--                       kasus/benchmark ESG karena konsisten unggul
--                       di setiap tahun evaluasi yang dimilikinya?"
-- =====================================================================
SELECT
    nama_perusahaan,
    sektor,
    COUNT(*)                          AS jumlah_tahun_dinilai,
    MIN(total_skor_esg)               AS skor_terendah_tercatat,
    GROUP_CONCAT(DISTINCT peringkat_esg) AS daftar_peringkat
FROM v_ringkasan_skor_perusahaan
GROUP BY company_id, nama_perusahaan, sektor
HAVING COUNT(*) >= 2
   AND SUM(CASE WHEN urutan_peringkat > 2 THEN 1 ELSE 0 END) = 0   -- 1=AAA, 2=AA
ORDER BY skor_terendah_tercatat DESC
LIMIT 15;


-- =====================================================================
-- Q13. Ringkasan Eksekutif (Executive Summary) - Satu Baris KPI Utama
-- Pertanyaan bisnis : "Berikan ringkasan angka-angka kunci data mart
--                       ini untuk slide pembuka laporan manajemen."
-- =====================================================================
SELECT
    (SELECT COUNT(*) FROM dim_perusahaan)                              AS total_perusahaan,
    (SELECT COUNT(DISTINCT sektor) FROM dim_perusahaan)                AS total_sektor,
    (SELECT COUNT(DISTINCT wilayah_operasional) FROM dim_perusahaan)   AS total_wilayah,
    (SELECT COUNT(*) FROM fact_penilaian_tahunan)                      AS total_penilaian_tahunan,
    (SELECT ROUND(AVG(total_skor_esg), 2) FROM fact_penilaian_tahunan) AS rata_rata_skor_esg_keseluruhan,
    (SELECT COUNT(*) FROM fact_catatan_aktivitas)                      AS total_catatan_aktivitas,
    (SELECT ROUND(100.0 * SUM(CASE WHEN status_kepatuhan = 'Patuh' THEN 1 ELSE 0 END)
            / COUNT(*), 2) FROM fact_catatan_aktivitas)                AS persentase_kepatuhan_keseluruhan,
    (SELECT SUM(biaya_mitigasi_idr) FROM fact_catatan_aktivitas)       AS total_biaya_mitigasi_idr;


-- =====================================================================
-- Q14. Efisiensi Biaya Mitigasi: Biaya per Poin Realisasi
-- Pertanyaan bisnis : "Sektor mana yang paling efisien secara biaya
--                       dalam mencapai realisasi metrik ESG-nya?"
-- Catatan           : biaya dibagi dengan rata-rata nilai realisasi
--                       sebagai proxy sederhana efisiensi biaya.
-- =====================================================================
SELECT
    p.sektor,
    ROUND(AVG(a.nilai_realisasi), 2)                       AS rata_rata_realisasi,
    SUM(a.biaya_mitigasi_idr)                              AS total_biaya_idr,
    ROUND(SUM(a.biaya_mitigasi_idr) * 1.0
          / NULLIF(AVG(a.nilai_realisasi), 0), 0)          AS biaya_per_poin_realisasi_idr
FROM fact_catatan_aktivitas a
JOIN dim_perusahaan p ON a.company_id = p.company_id
GROUP BY p.sektor
ORDER BY biaya_per_poin_realisasi_idr ASC;


-- =====================================================================
-- Q15. Ringkasan Kepatuhan per Pilar ESG (Environmental/Social/Governance)
-- Pertanyaan bisnis : "Dari tiga pilar ESG, mana yang tingkat
--                       kepatuhannya paling rendah secara keseluruhan?"
-- =====================================================================
SELECT
    m.pilar,
    COUNT(*)                                                          AS total_catatan,
    SUM(CASE WHEN a.status_kepatuhan = 'Patuh' THEN 1 ELSE 0 END)     AS jumlah_patuh,
    ROUND(100.0 * SUM(CASE WHEN a.status_kepatuhan = 'Patuh' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                              AS persentase_patuh,
    ROUND(AVG(a.nilai_realisasi), 2)                                  AS rata_rata_realisasi
FROM fact_catatan_aktivitas a
JOIN dim_metrik_esg m ON a.metric_id = m.metric_id
GROUP BY m.pilar
ORDER BY persentase_patuh ASC;

-- =====================================================================
-- Selesai. Lihat README.md bagian "Contoh Hasil & Insight" untuk
-- ringkasan temuan dari query-query di atas.
-- =====================================================================
