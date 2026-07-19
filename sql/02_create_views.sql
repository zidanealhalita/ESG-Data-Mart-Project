-- =====================================================================
-- ESG DATA MART - REPORTING VIEWS
-- =====================================================================
-- Penulis  : Muhammad Zidane Alhalita
-- Deskripsi:
--   View-view berikut adalah lapisan semantik siap-pakai (semantic /
--   presentation layer) di atas star schema. Tujuannya agar tim
--   pengguna bisnis (MIS/Reporting) tidak perlu menulis ulang JOIN
--   yang sama berkali-kali, cukup SELECT dari view ini.
--
-- Prasyarat: jalankan setelah 01_create_schema.sql dan setelah data
--            dimuat oleh ETL (etl/etl_pipeline.py).
-- =====================================================================

-- ---------------------------------------------------------------------
-- v_ringkasan_skor_perusahaan
-- Menggabungkan setiap penilaian tahunan dengan profil perusahaan
-- dan atribut peringkat, siap dipakai untuk laporan eksekutif.
-- ---------------------------------------------------------------------
CREATE VIEW v_ringkasan_skor_perusahaan AS
SELECT
    f.fact_score_id,
    p.company_id,
    p.nama_perusahaan,
    p.sektor,
    p.wilayah_operasional,
    p.tahun_listing,
    f.tahun_evaluasi,
    f.skor_environmental,
    f.skor_social,
    f.skor_governance,
    f.total_skor_esg,
    f.peringkat_esg,
    r.urutan_peringkat,
    r.kategori_risiko
FROM fact_penilaian_tahunan f
JOIN dim_perusahaan p     ON f.company_id = p.company_id
JOIN dim_peringkat_esg r  ON f.peringkat_esg = r.peringkat_esg;

-- ---------------------------------------------------------------------
-- v_kepatuhan_bulanan_sektor
-- Ringkasan tingkat kepatuhan aktivitas ESG per sektor & bulan,
-- lengkap dengan estimasi biaya mitigasi.
-- ---------------------------------------------------------------------
CREATE VIEW v_kepatuhan_bulanan_sektor AS
SELECT
    p.sektor,
    w.bulan,
    w.nama_bulan,
    w.kuartal,
    COUNT(*)                                                         AS total_catatan,
    SUM(CASE WHEN a.status_kepatuhan = 'Patuh' THEN 1 ELSE 0 END)    AS jumlah_patuh,
    ROUND(100.0 * SUM(CASE WHEN a.status_kepatuhan = 'Patuh' THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                             AS persentase_patuh,
    ROUND(AVG(a.nilai_realisasi), 2)                                 AS rata_rata_realisasi,
    SUM(a.biaya_mitigasi_idr)                                        AS total_biaya_mitigasi_idr
FROM fact_catatan_aktivitas a
JOIN dim_perusahaan p    ON a.company_id = p.company_id
JOIN dim_waktu_bulan w   ON a.bulan = w.bulan
GROUP BY p.sektor, w.bulan, w.nama_bulan, w.kuartal;

-- ---------------------------------------------------------------------
-- v_tren_skor_tahunan_sektor
-- Rata-rata skor ESG per sektor per tahun evaluasi -> untuk grafik tren.
-- ---------------------------------------------------------------------
CREATE VIEW v_tren_skor_tahunan_sektor AS
SELECT
    p.sektor,
    f.tahun_evaluasi,
    COUNT(*)                              AS jumlah_perusahaan_dinilai,
    ROUND(AVG(f.skor_environmental), 2)   AS avg_skor_environmental,
    ROUND(AVG(f.skor_social), 2)          AS avg_skor_social,
    ROUND(AVG(f.skor_governance), 2)      AS avg_skor_governance,
    ROUND(AVG(f.total_skor_esg), 2)       AS avg_total_skor_esg
FROM fact_penilaian_tahunan f
JOIN dim_perusahaan p ON f.company_id = p.company_id
GROUP BY p.sektor, f.tahun_evaluasi;

-- ---------------------------------------------------------------------
-- v_gap_kepatuhan_metrik
-- Membandingkan rata-rata realisasi tiap metrik terhadap target
-- kepatuhannya -> untuk menemukan metrik ESG yang paling bermasalah.
-- ---------------------------------------------------------------------
CREATE VIEW v_gap_kepatuhan_metrik AS
SELECT
    m.metric_id,
    m.pilar,
    m.nama_metrik,
    m.target_kepatuhan_persen,
    COUNT(*)                                                        AS jumlah_catatan,
    ROUND(AVG(a.nilai_realisasi), 2)                                AS rata_rata_realisasi,
    ROUND(AVG(a.nilai_realisasi) - m.target_kepatuhan_persen, 2)    AS gap_terhadap_target,
    SUM(CASE WHEN a.status_kepatuhan = 'Perlu Evaluasi' THEN 1 ELSE 0 END) AS jumlah_perlu_evaluasi
FROM fact_catatan_aktivitas a
JOIN dim_metrik_esg m ON a.metric_id = m.metric_id
GROUP BY m.metric_id, m.pilar, m.nama_metrik, m.target_kepatuhan_persen;

-- ---------------------------------------------------------------------
-- v_biaya_mitigasi_pilar
-- Total & rata-rata biaya mitigasi dikelompokkan per pilar ESG dan
-- sektor perusahaan -> mendukung analisis efisiensi biaya kepatuhan.
-- ---------------------------------------------------------------------
CREATE VIEW v_biaya_mitigasi_pilar AS
SELECT
    p.sektor,
    m.pilar,
    COUNT(*)                            AS jumlah_aktivitas,
    SUM(a.biaya_mitigasi_idr)           AS total_biaya_idr,
    ROUND(AVG(a.biaya_mitigasi_idr), 0) AS rata_rata_biaya_idr
FROM fact_catatan_aktivitas a
JOIN dim_perusahaan p  ON a.company_id = p.company_id
JOIN dim_metrik_esg m  ON a.metric_id = m.metric_id
GROUP BY p.sektor, m.pilar;

-- =====================================================================
-- Selesai. Lihat sql/03_analytical_queries.sql untuk contoh laporan
-- analitis yang memakai skema & view di atas.
-- =====================================================================
