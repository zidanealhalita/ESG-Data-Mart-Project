#!/usr/bin/env python3
# =====================================================================
# ESG DATA MART - ETL PIPELINE
# =====================================================================
# Proyek   : ESG Compliance & Performance Data Mart
# Penulis  : Muhammad Zidane Alhalita
# Deskripsi:
#   Skrip ini menjalankan proses ETL (Extract, Transform, Load) penuh:
#
#     EXTRACT   -> membaca 4 file CSV sumber dari data/raw/
#     TRANSFORM -> validasi kualitas data (null, duplikat, referential
#                  integrity), pembersihan tipe data, dan pembuatan
#                  dua dimensi turunan (dim_waktu_bulan & dim_peringkat_esg)
#     LOAD      -> membangun ulang skema (sql/01_create_schema.sql),
#                  memuat seluruh dimensi lalu tabel fakta ke dalam
#                  database SQLite data/esg_data_mart.db, kemudian
#                  membuat reporting views (sql/02_create_views.sql)
#
#   Setiap tahap mencatat log ke konsol dan ke file etl/etl_log.txt
#   agar proses dapat diaudit (jejak lazim pada praktik MIS/Data Mart).
#
# Cara pakai:
#   python3 etl/etl_pipeline.py
# =====================================================================

import logging
import sqlite3
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------
# Konfigurasi path proyek
# ---------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "data" / "esg_data_mart.db"
SQL_DIR = PROJECT_ROOT / "sql"
LOG_PATH = PROJECT_ROOT / "etl" / "etl_log.txt"

SCHEMA_SQL = SQL_DIR / "01_create_schema.sql"
VIEWS_SQL = SQL_DIR / "02_create_views.sql"

# ---------------------------------------------------------------------
# Konfigurasi logging (tampil di konsol + tersimpan di file log)
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("etl_pipeline")

BULAN_ID = [
    (1, "Januari", "Jan", "Q1", "Semester 1"),
    (2, "Februari", "Feb", "Q1", "Semester 1"),
    (3, "Maret", "Mar", "Q1", "Semester 1"),
    (4, "April", "Apr", "Q2", "Semester 1"),
    (5, "Mei", "Mei", "Q2", "Semester 1"),
    (6, "Juni", "Jun", "Q2", "Semester 1"),
    (7, "Juli", "Jul", "Q3", "Semester 2"),
    (8, "Agustus", "Agu", "Q3", "Semester 2"),
    (9, "September", "Sep", "Q3", "Semester 2"),
    (10, "Oktober", "Okt", "Q4", "Semester 2"),
    (11, "November", "Nov", "Q4", "Semester 2"),
    (12, "Desember", "Des", "Q4", "Semester 2"),
]

# Urutan peringkat ESG dari terbaik ke terendah, dipetakan ke kategori
# risiko kepatuhan agar laporan dapat diurutkan & dikelompokkan dengan benar.
PERINGKAT_ESG_REF = [
    # (peringkat, urutan, kategori_risiko, deskripsi)
    ("AAA", 1, "Rendah", "Kinerja ESG sangat unggul, praktik terbaik di kelasnya"),
    ("AA", 2, "Rendah", "Kinerja ESG unggul, di atas rata-rata industri"),
    ("A", 3, "Sedang", "Kinerja ESG baik, memenuhi ekspektasi standar"),
    ("BBB", 4, "Sedang", "Kinerja ESG cukup, ada ruang perbaikan signifikan"),
    ("BB", 5, "Tinggi", "Kinerja ESG di bawah standar, perlu tindakan korektif segera"),
]


# =====================================================================
# EXTRACT
# =====================================================================
def extract() -> dict[str, pd.DataFrame]:
    log.info("=" * 70)
    log.info("TAHAP 1/3: EXTRACT - membaca file CSV sumber dari %s", RAW_DIR)
    log.info("=" * 70)

    files = {
        "dim_perusahaan": RAW_DIR / "dim_perusahaan.csv",
        "dim_metrik_esg": RAW_DIR / "dim_metrik_esg.csv",
        "fact_penilaian_tahunan": RAW_DIR / "fact_penilaian_tahunan.csv",
        "fact_catatan_aktivitas": RAW_DIR / "fact_catatan_aktivitas.csv",
    }

    dataframes = {}
    for name, path in files.items():
        if not path.exists():
            log.error("File sumber tidak ditemukan: %s", path)
            raise FileNotFoundError(path)
        df = pd.read_csv(path)
        dataframes[name] = df
        log.info("Berhasil membaca %-26s -> %5d baris, %2d kolom", name, len(df), df.shape[1])

    return dataframes


# =====================================================================
# TRANSFORM (termasuk data quality checks)
# =====================================================================
def validate_data_quality(dfs: dict[str, pd.DataFrame]) -> None:
    log.info("-" * 70)
    log.info("Menjalankan pemeriksaan kualitas data (data quality checks)")
    log.info("-" * 70)

    issues_found = 0

    # 1) Cek nilai kosong (null) per tabel
    for name, df in dfs.items():
        null_counts = df.isnull().sum()
        total_nulls = int(null_counts.sum())
        if total_nulls > 0:
            issues_found += 1
            log.warning("[%s] Ditemukan %d nilai kosong:\n%s", name, total_nulls, null_counts[null_counts > 0])
        else:
            log.info("[%-26s] OK - tidak ada nilai kosong", name)

    # 2) Cek baris duplikat penuh
    for name, df in dfs.items():
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            issues_found += 1
            log.warning("[%s] Ditemukan %d baris duplikat penuh", name, dup_count)
        else:
            log.info("[%-26s] OK - tidak ada baris duplikat", name)

    # 3) Cek duplikat primary key
    pk_map = {
        "dim_perusahaan": "company_id",
        "dim_metrik_esg": "metric_id",
        "fact_penilaian_tahunan": "fact_score_id",
        "fact_catatan_aktivitas": "fact_activity_id",
    }
    for name, pk in pk_map.items():
        dup_pk = int(dfs[name][pk].duplicated().sum())
        if dup_pk > 0:
            issues_found += 1
            log.warning("[%s] Ditemukan %d primary key (%s) duplikat", name, dup_pk, pk)
        else:
            log.info("[%-26s] OK - primary key '%s' unik", name, pk)

    # 4) Cek referential integrity (foreign key orphan check)
    orphan_company_score = set(dfs["fact_penilaian_tahunan"]["company_id"]) - set(
        dfs["dim_perusahaan"]["company_id"]
    )
    orphan_company_activity = set(dfs["fact_catatan_aktivitas"]["company_id"]) - set(
        dfs["dim_perusahaan"]["company_id"]
    )
    orphan_metric_activity = set(dfs["fact_catatan_aktivitas"]["metric_id"]) - set(
        dfs["dim_metrik_esg"]["metric_id"]
    )

    for label, orphan_set in [
        ("fact_penilaian_tahunan.company_id -> dim_perusahaan", orphan_company_score),
        ("fact_catatan_aktivitas.company_id -> dim_perusahaan", orphan_company_activity),
        ("fact_catatan_aktivitas.metric_id -> dim_metrik_esg", orphan_metric_activity),
    ]:
        if orphan_set:
            issues_found += 1
            log.warning("Referential integrity GAGAL pada %s: %d id tidak ditemukan", label, len(orphan_set))
        else:
            log.info("Referential integrity OK  : %s", label)

    # 5) Cek konsistensi formula total_skor_esg = rata-rata 3 pilar
    fpt = dfs["fact_penilaian_tahunan"]
    calc_total = (fpt["skor_environmental"] + fpt["skor_social"] + fpt["skor_governance"]) / 3
    mismatch = (calc_total.round(2) - fpt["total_skor_esg"].round(2)).abs() > 0.02
    if mismatch.any():
        issues_found += 1
        log.warning("Ditemukan %d baris total_skor_esg yang tidak konsisten dengan rata-rata 3 pilar", mismatch.sum())
    else:
        log.info("Konsistensi formula OK   : total_skor_esg = rata-rata(E, S, G) pada seluruh baris")

    # 6) Cek rentang nilai bulan (harus 1-12)
    bulan_invalid = ~dfs["fact_catatan_aktivitas"]["bulan"].between(1, 12)
    if bulan_invalid.any():
        issues_found += 1
        log.warning("Ditemukan %d baris dengan nilai bulan di luar rentang 1-12", bulan_invalid.sum())
    else:
        log.info("Rentang nilai 'bulan'    OK  : seluruh nilai berada pada 1-12")

    if issues_found == 0:
        log.info("HASIL: seluruh pemeriksaan kualitas data LULUS tanpa temuan.")
    else:
        log.warning("HASIL: ditemukan %d kategori isu kualitas data (lihat detail di atas).", issues_found)


def transform(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    log.info("=" * 70)
    log.info("TAHAP 2/3: TRANSFORM - validasi kualitas data & pembuatan dimensi turunan")
    log.info("=" * 70)

    validate_data_quality(dfs)

    log.info("-" * 70)
    log.info("Membangun dimensi turunan (derived dimensions)")
    log.info("-" * 70)

    # dim_waktu_bulan: dimensi kalender bulan, dibangun secara statis
    # karena fact_catatan_aktivitas hanya menyimpan nomor bulan (1-12)
    # tanpa informasi tahun.
    dim_waktu_bulan = pd.DataFrame(
        BULAN_ID, columns=["bulan", "nama_bulan", "nama_bulan_singkat", "kuartal", "semester"]
    )
    log.info("Dimensi 'dim_waktu_bulan'   dibuat -> %d baris (bulan 1-12)", len(dim_waktu_bulan))

    # dim_peringkat_esg: dimensi referensi urutan & kategori risiko
    # peringkat ESG, divalidasi terhadap nilai unik yang benar-benar
    # muncul pada data fakta agar tidak ada baris referensi yang tidak terpakai.
    actual_ratings = set(dfs["fact_penilaian_tahunan"]["peringkat_esg"].unique())
    dim_peringkat_esg = pd.DataFrame(
        PERINGKAT_ESG_REF, columns=["peringkat_esg", "urutan_peringkat", "kategori_risiko", "deskripsi"]
    )
    missing_ratings = actual_ratings - set(dim_peringkat_esg["peringkat_esg"])
    if missing_ratings:
        log.warning(
            "Ditemukan peringkat_esg pada data fakta yang belum ada di tabel referensi: %s",
            missing_ratings,
        )
    else:
        log.info(
            "Dimensi 'dim_peringkat_esg' dibuat -> %d baris, tervalidasi cocok dengan data fakta (%s)",
            len(dim_peringkat_esg),
            ", ".join(sorted(actual_ratings)),
        )

    dfs["dim_waktu_bulan"] = dim_waktu_bulan
    dfs["dim_peringkat_esg"] = dim_peringkat_esg
    return dfs


# =====================================================================
# LOAD
# =====================================================================
def load(dfs: dict[str, pd.DataFrame]) -> None:
    log.info("=" * 70)
    log.info("TAHAP 3/3: LOAD - membangun skema & memuat data ke SQLite")
    log.info("=" * 70)

    if DB_PATH.exists():
        DB_PATH.unlink()
        log.info("Database lama ditemukan dan dihapus untuk pemuatan ulang bersih: %s", DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    try:
        # 1) Bangun skema (DDL) dari file SQL
        log.info("Menjalankan skrip skema: %s", SCHEMA_SQL.name)
        conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))

        # 2) Muat dimensi terlebih dahulu (urutan penting karena foreign key)
        load_order = [
            "dim_perusahaan",
            "dim_metrik_esg",
            "dim_waktu_bulan",
            "dim_peringkat_esg",
            "fact_penilaian_tahunan",
            "fact_catatan_aktivitas",
        ]
        for table in load_order:
            df = dfs[table]
            df.to_sql(table, conn, if_exists="append", index=False)
            log.info("Dimuat ke tabel %-26s -> %5d baris", table, len(df))

        conn.commit()

        # 3) Bangun reporting views
        log.info("Menjalankan skrip views : %s", VIEWS_SQL.name)
        conn.executescript(VIEWS_SQL.read_text(encoding="utf-8"))
        conn.commit()

        # 4) Verifikasi akhir: hitung baris tiap tabel & view utama
        log.info("-" * 70)
        log.info("Verifikasi akhir jumlah baris pada database")
        log.info("-" * 70)
        cur = conn.cursor()
        for table in load_order:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            log.info("  %-26s : %5d baris", table, count)

    except sqlite3.Error as e:
        conn.rollback()
        log.error("Terjadi kesalahan SQLite, transaksi dibatalkan: %s", e)
        raise
    finally:
        conn.close()

    log.info("Database ESG Data Mart berhasil dibuat di: %s", DB_PATH)


# =====================================================================
# MAIN
# =====================================================================
def main() -> None:
    log.info("MEMULAI PIPELINE ETL - ESG DATA MART")
    log.info("Penulis proyek: Muhammad Zidane Alhalita")
    dfs = extract()
    dfs = transform(dfs)
    load(dfs)
    log.info("PIPELINE ETL SELESAI. Log lengkap tersimpan di: %s", LOG_PATH)


if __name__ == "__main__":
    main()
