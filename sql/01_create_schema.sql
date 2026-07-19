-- =====================================================================
-- ESG DATA MART - SCHEMA DDL (Data Definition Language)
-- =====================================================================
-- Proyek   : ESG Compliance & Performance Data Mart
-- Penulis  : Muhammad Zidane Alhalita
-- Dibuat   : 2026
-- Engine   : SQLite 3 (portable, kompatibel dengan sedikit penyesuaian
--            ke PostgreSQL / MySQL / SQL Server)
--
-- Deskripsi:
--   Skrip ini membangun struktur data mart bermodel dimensional
--   (star schema / fact constellation) untuk analisis kinerja dan
--   kepatuhan ESG (Environmental, Social, Governance) perusahaan.
--
--   Terdapat 2 tabel fakta (fact table) yang berbagi dimensi
--   perusahaan yang sama, sehingga desain ini disebut
--   "fact constellation" / "galaxy schema":
--
--       dim_perusahaan ─┬─> fact_penilaian_tahunan ──> dim_peringkat_esg
--                        └─> fact_catatan_aktivitas ──> dim_metrik_esg
--                                                    └─> dim_waktu_bulan
--
-- Urutan eksekusi: jalankan file ini SEBELUM 02_create_views.sql
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- Bersihkan objek lama (agar skrip dapat dijalankan berulang / idempotent)
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS v_ringkasan_skor_perusahaan;
DROP VIEW IF EXISTS v_kepatuhan_bulanan_sektor;
DROP VIEW IF EXISTS v_tren_skor_tahunan_sektor;
DROP VIEW IF EXISTS v_gap_kepatuhan_metrik;
DROP VIEW IF EXISTS v_biaya_mitigasi_pilar;

DROP TABLE IF EXISTS fact_catatan_aktivitas;
DROP TABLE IF EXISTS fact_penilaian_tahunan;
DROP TABLE IF EXISTS dim_perusahaan;
DROP TABLE IF EXISTS dim_metrik_esg;
DROP TABLE IF EXISTS dim_waktu_bulan;
DROP TABLE IF EXISTS dim_peringkat_esg;

-- =====================================================================
-- 1. DIMENSION TABLES
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1.1 dim_perusahaan
--     Grain     : 1 baris = 1 perusahaan
--     Sumber    : dim_perusahaan.csv (data master, dipakai apa adanya)
-- ---------------------------------------------------------------------
CREATE TABLE dim_perusahaan (
    company_id              TEXT    PRIMARY KEY,
    nama_perusahaan         TEXT    NOT NULL,
    sektor                  TEXT    NOT NULL,
    wilayah_operasional     TEXT    NOT NULL,
    tahun_listing           INTEGER NOT NULL
        CHECK (tahun_listing BETWEEN 1990 AND 2100)
);

CREATE INDEX idx_perusahaan_sektor  ON dim_perusahaan (sektor);
CREATE INDEX idx_perusahaan_wilayah ON dim_perusahaan (wilayah_operasional);

-- ---------------------------------------------------------------------
-- 1.2 dim_metrik_esg
--     Grain     : 1 baris = 1 metrik ESG yang diukur
--     Sumber    : dim_metrik_esg.csv (data master, dipakai apa adanya)
-- ---------------------------------------------------------------------
CREATE TABLE dim_metrik_esg (
    metric_id                  TEXT    PRIMARY KEY,
    pilar                      TEXT    NOT NULL
        CHECK (pilar IN ('Environmental', 'Social', 'Governance')),
    nama_metrik                TEXT    NOT NULL,
    satuan                     TEXT,
    target_kepatuhan_persen    REAL    NOT NULL
        CHECK (target_kepatuhan_persen BETWEEN 0 AND 100)
);

CREATE INDEX idx_metrik_pilar ON dim_metrik_esg (pilar);

-- ---------------------------------------------------------------------
-- 1.3 dim_waktu_bulan  (dimensi turunan / derived dimension)
--     Grain     : 1 baris = 1 bulan kalender (1-12)
--     Sumber    : dibangun oleh ETL, bukan dari file CSV mentah,
--                 karena fact_catatan_aktivitas hanya menyimpan
--                 nomor bulan tanpa tahun (lihat catatan keterbatasan
--                 data pada README.md, bagian "Asumsi & Keterbatasan").
-- ---------------------------------------------------------------------
CREATE TABLE dim_waktu_bulan (
    bulan               INTEGER PRIMARY KEY CHECK (bulan BETWEEN 1 AND 12),
    nama_bulan          TEXT    NOT NULL,
    nama_bulan_singkat  TEXT    NOT NULL,
    kuartal             TEXT    NOT NULL,
    semester            TEXT    NOT NULL
);

-- ---------------------------------------------------------------------
-- 1.4 dim_peringkat_esg  (dimensi referensi / lookup dimension)
--     Grain     : 1 baris = 1 kategori peringkat ESG
--     Sumber    : dibangun oleh ETL berdasarkan nilai unik kolom
--                 peringkat_esg pada fact_penilaian_tahunan.csv,
--                 diperkaya dengan urutan & kategori risiko agar
--                 laporan dapat diurutkan & dikelompokkan dengan benar.
-- ---------------------------------------------------------------------
CREATE TABLE dim_peringkat_esg (
    peringkat_esg      TEXT    PRIMARY KEY,
    urutan_peringkat    INTEGER NOT NULL,   -- 1 = terbaik (AAA) ... 5 = terendah (BB)
    kategori_risiko     TEXT    NOT NULL,   -- Rendah / Sedang / Tinggi
    deskripsi            TEXT
);

-- =====================================================================
-- 2. FACT TABLES
-- =====================================================================

-- ---------------------------------------------------------------------
-- 2.1 fact_penilaian_tahunan
--     Grain     : 1 baris = 1 penilaian ESG untuk 1 perusahaan
--                 pada 1 tahun evaluasi
--     Tipe fakta: semi-aditif (skor tidak boleh dijumlah lintas tahun,
--                 tetapi bisa dirata-ratakan / dibandingkan antar waktu)
--     Sumber    : fact_penilaian_tahunan.csv
-- ---------------------------------------------------------------------
CREATE TABLE fact_penilaian_tahunan (
    fact_score_id        TEXT    PRIMARY KEY,
    company_id            TEXT    NOT NULL,
    tahun_evaluasi        INTEGER NOT NULL,      -- degenerate dimension (grain tahun)
    skor_environmental    INTEGER NOT NULL CHECK (skor_environmental BETWEEN 0 AND 100),
    skor_social           INTEGER NOT NULL CHECK (skor_social BETWEEN 0 AND 100),
    skor_governance       INTEGER NOT NULL CHECK (skor_governance BETWEEN 0 AND 100),
    total_skor_esg        REAL    NOT NULL CHECK (total_skor_esg BETWEEN 0 AND 100),
    peringkat_esg         TEXT    NOT NULL,

    FOREIGN KEY (company_id)   REFERENCES dim_perusahaan (company_id),
    FOREIGN KEY (peringkat_esg) REFERENCES dim_peringkat_esg (peringkat_esg)
);

CREATE INDEX idx_fpt_company ON fact_penilaian_tahunan (company_id);
CREATE INDEX idx_fpt_tahun   ON fact_penilaian_tahunan (tahun_evaluasi);
CREATE INDEX idx_fpt_peringkat ON fact_penilaian_tahunan (peringkat_esg);

-- ---------------------------------------------------------------------
-- 2.2 fact_catatan_aktivitas
--     Grain     : 1 baris = 1 catatan realisasi 1 metrik ESG untuk
--                 1 perusahaan pada 1 bulan
--     Tipe fakta: aditif (biaya_mitigasi_idr bisa dijumlah;
--                 nilai_realisasi sebaiknya dirata-ratakan)
--     Sumber    : fact_catatan_aktivitas.csv
-- ---------------------------------------------------------------------
CREATE TABLE fact_catatan_aktivitas (
    fact_activity_id     TEXT    PRIMARY KEY,
    company_id            TEXT    NOT NULL,
    metric_id             TEXT    NOT NULL,
    bulan                 INTEGER NOT NULL,
    nilai_realisasi        REAL    NOT NULL,
    status_kepatuhan       TEXT    NOT NULL
        CHECK (status_kepatuhan IN ('Patuh', 'Perlu Evaluasi')),
    biaya_mitigasi_idr     INTEGER NOT NULL CHECK (biaya_mitigasi_idr >= 0),

    FOREIGN KEY (company_id) REFERENCES dim_perusahaan (company_id),
    FOREIGN KEY (metric_id)  REFERENCES dim_metrik_esg (metric_id),
    FOREIGN KEY (bulan)      REFERENCES dim_waktu_bulan (bulan)
);

CREATE INDEX idx_fca_company ON fact_catatan_aktivitas (company_id);
CREATE INDEX idx_fca_metric  ON fact_catatan_aktivitas (metric_id);
CREATE INDEX idx_fca_bulan   ON fact_catatan_aktivitas (bulan);
CREATE INDEX idx_fca_status  ON fact_catatan_aktivitas (status_kepatuhan);

-- =====================================================================
-- Selesai. Lanjutkan dengan 02_create_views.sql setelah data dimuat.
-- =====================================================================
