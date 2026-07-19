#!/usr/bin/env python3
"""
ESG Data Mart — Dashboard Interaktif (Streamlit)
==================================================
Penulis: Muhammad Zidane Alhalita

Berbeda dengan `reports/dashboard.html` (data statis yang di-embed),
dashboard ini melakukan QUERY LANGSUNG ke database SQLite setiap kali
pengguna mengubah filter — mensimulasikan alat self-service BI yang
umum dipakai tim data/MIS untuk eksplorasi ad-hoc.

Cara menjalankan:
    streamlit run app/streamlit_app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import streamlit as st

# =====================================================================
# KONFIGURASI HALAMAN & PATH
# =====================================================================
st.set_page_config(
    page_title="ESG Data Mart — Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "esg_data_mart.db"

# Palet warna konsisten dengan reports/dashboard.html
COLOR_ENV = "#4F9D6E"
COLOR_SOC = "#4A85B8"
COLOR_GOV = "#C9A036"
COLOR_DANGER = "#C1554A"
SEKTOR_PALETTE = ["#4F9D6E", "#4A85B8", "#C9A036", "#C1554A", "#8B7BC7", "#3FB8AF"]
RATING_COLOR = {"AAA": COLOR_ENV, "AA": COLOR_ENV, "A": COLOR_SOC, "BBB": COLOR_GOV, "BB": COLOR_DANGER}
PLOTLY_TEMPLATE = "plotly_dark"

# =====================================================================
# CSS KUSTOM — menyamakan nuansa visual dengan reports/dashboard.html
# =====================================================================
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
    <style>
        .stApp { background-color: #0E1A16; }
        h1, h2, h3 { font-family: 'Fraunces', serif !important; }
        [data-testid="stMetricValue"] { font-family: 'IBM Plex Mono', monospace; }
        [data-testid="stMetric"] {
            background-color: #16241F;
            border: 1px solid #26382F;
            border-radius: 12px;
            padding: 14px 16px;
        }
        .pillar-badge {
            font-family: 'IBM Plex Mono', monospace; font-size: 12px; letter-spacing: .04em;
            padding: 3px 10px; border-radius: 100px; display: inline-flex; align-items: center; gap: 6px;
            border: 1px solid #26382F; margin-right: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# PASTIKAN DATABASE TERSEDIA (AUTO-BUILD JIKA BELUM ADA)
# =====================================================================
# Konteks: data/esg_data_mart.db sengaja TIDAK di-commit ke git (lihat
# .gitignore) karena ia adalah build artifact, bukan sumber data asli.
# Saat di-deploy ke lingkungan baru (mis. Streamlit Community Cloud),
# file ini belum ada di clone repo tsb. Alih-alih menyuruh pengguna
# menjalankan ETL secara manual, dashboard membangunnya sendiri di
# awal sesi — cukup sekali per instance berkat @st.cache_resource,
# dan bersumber dari data/raw/*.csv yang memang ikut ter-commit.
@st.cache_resource
def ensure_database():
    if DB_PATH.exists():
        return "sudah_ada"

    import importlib.util

    etl_script = PROJECT_ROOT / "etl" / "etl_pipeline.py"
    spec = importlib.util.spec_from_file_location("etl_pipeline", etl_script)
    etl_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(etl_module)
    etl_module.main()
    return "baru_dibangun"


with st.spinner("Menyiapkan database dari data sumber (hanya dijalankan sekali)..."):
    db_status = ensure_database()

if db_status == "baru_dibangun":
    st.toast("Database berhasil dibangun dari data/raw/*.csv", icon="✅")

# =====================================================================
# KONEKSI DATABASE (READ-ONLY, DI-CACHE SELAMA SESI)
# =====================================================================
@st.cache_resource
def get_connection():
    if not DB_PATH.exists():
        return None
    # Mode read-only URI agar dashboard tidak pernah menulis ke database
    uri = f"file:{DB_PATH}?mode=ro"
    return sqlite3.connect(uri, uri=True, check_same_thread=False)


conn = get_connection()

if conn is None:
    st.error(
        "Database tidak ditemukan dan gagal dibangun otomatis dari `data/raw/*.csv`.\n\n"
        "Pastikan folder `data/raw/` berisi ke-4 file CSV sumber, lalu coba jalankan "
        "manual dari root proyek:\n\n"
        "```bash\npython3 etl/etl_pipeline.py\n```"
    )
    st.stop()


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params)


def in_clause(values: list) -> str:
    """Menghasilkan placeholder '?,?,?' yang aman untuk klausa IN (...)."""
    return ",".join(["?"] * len(values))


# =====================================================================
# OPSI FILTER (di-cache karena jarang berubah)
# =====================================================================
@st.cache_data
def load_filter_options():
    sektor = run_query("SELECT DISTINCT sektor FROM dim_perusahaan ORDER BY sektor")["sektor"].tolist()
    wilayah = run_query(
        "SELECT DISTINCT wilayah_operasional FROM dim_perusahaan ORDER BY wilayah_operasional"
    )["wilayah_operasional"].tolist()
    tahun = run_query(
        "SELECT MIN(tahun_evaluasi) AS min_t, MAX(tahun_evaluasi) AS max_t FROM fact_penilaian_tahunan"
    ).iloc[0]
    return sektor, wilayah, int(tahun["min_t"]), int(tahun["max_t"])


all_sektor, all_wilayah, min_tahun, max_tahun = load_filter_options()
all_pilar = ["Environmental", "Social", "Governance"]

# =====================================================================
# SIDEBAR — FILTER
# =====================================================================
with st.sidebar:
    st.markdown("### 🌱 ESG Data Mart")
    st.caption("Dashboard interaktif · query langsung ke `esg_data_mart.db`")
    st.markdown("---")
    st.markdown("**Filter**")

    f_sektor = st.multiselect("Sektor", all_sektor, default=all_sektor)
    f_wilayah = st.multiselect("Wilayah Operasional", all_wilayah, default=all_wilayah)
    f_tahun = st.slider("Rentang Tahun Evaluasi", min_tahun, max_tahun, (min_tahun, max_tahun))
    f_pilar = st.multiselect("Pilar ESG (grafik aktivitas)", all_pilar, default=all_pilar)

    st.markdown("---")
    st.caption("Muhammad Zidane Alhalita — ESG Data Mart Project")

# Guard: jika filter kosong, hentikan render agar tidak error query IN ()
if not f_sektor or not f_wilayah or not f_pilar:
    st.warning("Pilih minimal satu opsi pada setiap filter di sidebar untuk menampilkan data.")
    st.stop()

# =====================================================================
# HEADER
# =====================================================================
st.title("Kondisi Kepatuhan & Kinerja ESG")
st.caption(
    f"Menampilkan {len(f_sektor)} sektor · {len(f_wilayah)} wilayah · "
    f"tahun evaluasi {f_tahun[0]}–{f_tahun[1]} · data live dari star schema data mart"
)

# =====================================================================
# QUERY: KPI RINGKASAN (mengikuti filter aktif)
# =====================================================================
kpi_sql = f"""
WITH skor AS (
    SELECT f.*, p.sektor, p.wilayah_operasional
    FROM fact_penilaian_tahunan f
    JOIN dim_perusahaan p ON f.company_id = p.company_id
    WHERE p.sektor IN ({in_clause(f_sektor)})
      AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
      AND f.tahun_evaluasi BETWEEN ? AND ?
),
aktivitas AS (
    SELECT a.*, p.sektor, p.wilayah_operasional, m.pilar
    FROM fact_catatan_aktivitas a
    JOIN dim_perusahaan p ON a.company_id = p.company_id
    JOIN dim_metrik_esg m ON a.metric_id = m.metric_id
    WHERE p.sektor IN ({in_clause(f_sektor)})
      AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
      AND m.pilar IN ({in_clause(f_pilar)})
)
SELECT
    (SELECT COUNT(DISTINCT company_id) FROM skor)                          AS jumlah_perusahaan,
    (SELECT ROUND(AVG(total_skor_esg), 2) FROM skor)                       AS avg_skor,
    (SELECT ROUND(100.0 * SUM(CASE WHEN status_kepatuhan='Patuh' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 2) FROM aktivitas)                      AS persen_patuh,
    (SELECT SUM(biaya_mitigasi_idr) FROM aktivitas)                        AS total_biaya
"""
kpi_params = (
    tuple(f_sektor) + tuple(f_wilayah) + (f_tahun[0], f_tahun[1])
    + tuple(f_sektor) + tuple(f_wilayah) + tuple(f_pilar)
)
kpi = run_query(kpi_sql, kpi_params).iloc[0]


def fmt_idr(n):
    if n is None or pd.isna(n):
        return "Rp 0"
    n = float(n)
    if n >= 1e12:
        return f"Rp {n/1e12:,.2f} T"
    if n >= 1e9:
        return f"Rp {n/1e9:,.2f} M"
    if n >= 1e6:
        return f"Rp {n/1e6:,.1f} Jt"
    return f"Rp {n:,.0f}"


c1, c2, c3, c4 = st.columns(4)
c1.metric("Perusahaan (dalam filter)", f"{int(kpi['jumlah_perusahaan']):,}".replace(",", "."))
c2.metric("Rata-rata Skor ESG", f"{kpi['avg_skor']:.2f}" if pd.notna(kpi["avg_skor"]) else "—")
c3.metric("Tingkat Kepatuhan", f"{kpi['persen_patuh']:.1f}%" if pd.notna(kpi["persen_patuh"]) else "—")
c4.metric("Total Biaya Mitigasi", fmt_idr(kpi["total_biaya"]))

st.markdown("")

# =====================================================================
# TABS
# =====================================================================
tab1, tab2, tab3 = st.tabs(["📈 Tren & Peringkat", "✅ Kepatuhan & Biaya", "🔍 Eksplorasi Perusahaan"])

# ---------------------------------------------------------------------
# TAB 1 — TREN & PERINGKAT
# ---------------------------------------------------------------------
with tab1:
    st.subheader("Tren Rata-rata Skor ESG per Sektor")
    tren_sql = f"""
        SELECT p.sektor, f.tahun_evaluasi, ROUND(AVG(f.total_skor_esg), 2) AS avg_total_skor_esg
        FROM fact_penilaian_tahunan f
        JOIN dim_perusahaan p ON f.company_id = p.company_id
        WHERE p.sektor IN ({in_clause(f_sektor)})
          AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
          AND f.tahun_evaluasi BETWEEN ? AND ?
        GROUP BY p.sektor, f.tahun_evaluasi
        ORDER BY p.sektor, f.tahun_evaluasi
    """
    df_tren = run_query(tren_sql, tuple(f_sektor) + tuple(f_wilayah) + (f_tahun[0], f_tahun[1]))

    if df_tren.empty:
        st.info("Tidak ada data pada kombinasi filter ini.")
    else:
        fig = px.line(
            df_tren, x="tahun_evaluasi", y="avg_total_skor_esg", color="sektor",
            markers=True, template=PLOTLY_TEMPLATE, color_discrete_sequence=SEKTOR_PALETTE,
            labels={"tahun_evaluasi": "Tahun Evaluasi", "avg_total_skor_esg": "Rata-rata Skor ESG", "sektor": "Sektor"},
        )
        fig.update_layout(height=380, legend=dict(orientation="h", y=-0.2), margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    colA, colB = st.columns(2)

    with colA:
        st.subheader("Distribusi Peringkat per Sektor")
        rating_sql = f"""
            SELECT p.sektor, f.peringkat_esg, COUNT(*) AS jumlah, r.urutan_peringkat
            FROM fact_penilaian_tahunan f
            JOIN dim_perusahaan p ON f.company_id = p.company_id
            JOIN dim_peringkat_esg r ON f.peringkat_esg = r.peringkat_esg
            WHERE p.sektor IN ({in_clause(f_sektor)})
              AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
              AND f.tahun_evaluasi BETWEEN ? AND ?
            GROUP BY p.sektor, f.peringkat_esg, r.urutan_peringkat
            ORDER BY r.urutan_peringkat
        """
        df_rating = run_query(rating_sql, tuple(f_sektor) + tuple(f_wilayah) + (f_tahun[0], f_tahun[1]))
        if df_rating.empty:
            st.info("Tidak ada data.")
        else:
            fig2 = px.bar(
                df_rating, x="sektor", y="jumlah", color="peringkat_esg", barmode="stack",
                template=PLOTLY_TEMPLATE, color_discrete_map=RATING_COLOR,
                category_orders={"peringkat_esg": ["AAA", "AA", "A", "BBB", "BB"]},
                labels={"sektor": "Sektor", "jumlah": "Jumlah Penilaian", "peringkat_esg": "Peringkat"},
            )
            fig2.update_layout(height=380, margin=dict(t=10))
            st.plotly_chart(fig2, use_container_width=True)

    with colB:
        st.subheader("Top 10 Skor ESG Tertinggi")
        top_sql = f"""
            SELECT p.nama_perusahaan AS Perusahaan, p.sektor AS Sektor,
                   f.total_skor_esg AS Skor, f.peringkat_esg AS Peringkat
            FROM fact_penilaian_tahunan f
            JOIN dim_perusahaan p ON f.company_id = p.company_id
            WHERE p.sektor IN ({in_clause(f_sektor)})
              AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
              AND f.tahun_evaluasi BETWEEN ? AND ?
            ORDER BY f.total_skor_esg DESC LIMIT 10
        """
        df_top = run_query(top_sql, tuple(f_sektor) + tuple(f_wilayah) + (f_tahun[0], f_tahun[1]))
        st.dataframe(df_top, use_container_width=True, hide_index=True, height=380)

# ---------------------------------------------------------------------
# TAB 2 — KEPATUHAN & BIAYA
# ---------------------------------------------------------------------
with tab2:
    st.subheader("Kepatuhan per Pilar ESG")
    pilar_sql = f"""
        SELECT m.pilar,
            ROUND(100.0 * SUM(CASE WHEN a.status_kepatuhan='Patuh' THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0), 2) AS persen_patuh,
            ROUND(AVG(a.nilai_realisasi), 2) AS avg_realisasi
        FROM fact_catatan_aktivitas a
        JOIN dim_perusahaan p ON a.company_id = p.company_id
        JOIN dim_metrik_esg m ON a.metric_id = m.metric_id
        WHERE p.sektor IN ({in_clause(f_sektor)})
          AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
          AND m.pilar IN ({in_clause(f_pilar)})
        GROUP BY m.pilar
    """
    df_pilar = run_query(pilar_sql, tuple(f_sektor) + tuple(f_wilayah) + tuple(f_pilar))
    pilar_colors = {"Environmental": COLOR_ENV, "Social": COLOR_SOC, "Governance": COLOR_GOV}

    if df_pilar.empty:
        st.info("Tidak ada data pada kombinasi filter ini.")
    else:
        cols = st.columns(len(df_pilar))
        for col, (_, row) in zip(cols, df_pilar.iterrows()):
            with col:
                fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=row["persen_patuh"],
                        number={"suffix": "%", "font": {"family": "IBM Plex Mono", "size": 32}},
                        gauge={
                            "axis": {"range": [0, 100], "tickcolor": "#8FA39A"},
                            "bar": {"color": pilar_colors.get(row["pilar"], COLOR_ENV)},
                            "bgcolor": "#16241F",
                            "borderwidth": 0,
                        },
                        title={"text": row["pilar"], "font": {"size": 14}},
                    )
                )
                fig.update_layout(height=220, margin=dict(t=40, b=10, l=20, r=20), template=PLOTLY_TEMPLATE)
                st.plotly_chart(fig, use_container_width=True)

    colC, colD = st.columns(2)

    with colC:
        st.subheader("Pola Kepatuhan Bulanan")
        bulan_sql = f"""
            SELECT w.bulan, w.nama_bulan_singkat,
                ROUND(100.0 * SUM(CASE WHEN a.status_kepatuhan='Patuh' THEN 1 ELSE 0 END)
                      / NULLIF(COUNT(*), 0), 2) AS persen_patuh
            FROM fact_catatan_aktivitas a
            JOIN dim_perusahaan p ON a.company_id = p.company_id
            JOIN dim_metrik_esg m ON a.metric_id = m.metric_id
            JOIN dim_waktu_bulan w ON a.bulan = w.bulan
            WHERE p.sektor IN ({in_clause(f_sektor)})
              AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
              AND m.pilar IN ({in_clause(f_pilar)})
            GROUP BY w.bulan, w.nama_bulan_singkat
            ORDER BY w.bulan
        """
        df_bulan = run_query(bulan_sql, tuple(f_sektor) + tuple(f_wilayah) + tuple(f_pilar))
        if df_bulan.empty:
            st.info("Tidak ada data.")
        else:
            fig3 = px.bar(
                df_bulan, x="nama_bulan_singkat", y="persen_patuh", template=PLOTLY_TEMPLATE,
                color_discrete_sequence=[COLOR_SOC],
                labels={"nama_bulan_singkat": "Bulan", "persen_patuh": "% Patuh"},
            )
            fig3.update_layout(height=340, margin=dict(t=10), yaxis_range=[0, 100])
            st.plotly_chart(fig3, use_container_width=True)

    with colD:
        st.subheader("Rata-rata Skor ESG per Wilayah")
        wilayah_sql = f"""
            SELECT p.wilayah_operasional, ROUND(AVG(f.total_skor_esg), 2) AS avg_skor
            FROM fact_penilaian_tahunan f
            JOIN dim_perusahaan p ON f.company_id = p.company_id
            WHERE p.sektor IN ({in_clause(f_sektor)})
              AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
              AND f.tahun_evaluasi BETWEEN ? AND ?
            GROUP BY p.wilayah_operasional
            ORDER BY avg_skor DESC
        """
        df_wilayah = run_query(wilayah_sql, tuple(f_sektor) + tuple(f_wilayah) + (f_tahun[0], f_tahun[1]))
        if df_wilayah.empty:
            st.info("Tidak ada data.")
        else:
            fig4 = px.bar(
                df_wilayah, x="avg_skor", y="wilayah_operasional", orientation="h",
                template=PLOTLY_TEMPLATE, color_discrete_sequence=[COLOR_ENV],
                labels={"avg_skor": "Rata-rata Skor ESG", "wilayah_operasional": ""},
            )
            fig4.update_layout(height=340, margin=dict(t=10), yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Total Biaya Mitigasi per Sektor & Pilar")
    biaya_sql = f"""
        SELECT p.sektor, m.pilar, SUM(a.biaya_mitigasi_idr) AS total_biaya
        FROM fact_catatan_aktivitas a
        JOIN dim_perusahaan p ON a.company_id = p.company_id
        JOIN dim_metrik_esg m ON a.metric_id = m.metric_id
        WHERE p.sektor IN ({in_clause(f_sektor)})
          AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
          AND m.pilar IN ({in_clause(f_pilar)})
        GROUP BY p.sektor, m.pilar
        ORDER BY p.sektor
    """
    df_biaya = run_query(biaya_sql, tuple(f_sektor) + tuple(f_wilayah) + tuple(f_pilar))
    if df_biaya.empty:
        st.info("Tidak ada data.")
    else:
        fig5 = px.bar(
            df_biaya, x="sektor", y="total_biaya", color="pilar", barmode="stack",
            template=PLOTLY_TEMPLATE, color_discrete_map=pilar_colors,
            labels={"sektor": "Sektor", "total_biaya": "Total Biaya Mitigasi (IDR)", "pilar": "Pilar"},
        )
        fig5.update_layout(height=380, margin=dict(t=10))
        st.plotly_chart(fig5, use_container_width=True)

# ---------------------------------------------------------------------
# TAB 3 — EKSPLORASI PERUSAHAAN
# ---------------------------------------------------------------------
with tab3:
    st.subheader("Cari & Eksplorasi Perusahaan")
    search_term = st.text_input("Cari nama perusahaan", placeholder="mis. PT Bumi Persada")

    explore_sql = f"""
        SELECT
            p.nama_perusahaan AS Perusahaan, p.sektor AS Sektor,
            p.wilayah_operasional AS Wilayah, p.tahun_listing AS "Tahun Listing",
            f.tahun_evaluasi AS "Tahun Evaluasi", f.skor_environmental AS "Skor E",
            f.skor_social AS "Skor S", f.skor_governance AS "Skor G",
            f.total_skor_esg AS "Total Skor", f.peringkat_esg AS Peringkat
        FROM fact_penilaian_tahunan f
        JOIN dim_perusahaan p ON f.company_id = p.company_id
        WHERE p.sektor IN ({in_clause(f_sektor)})
          AND p.wilayah_operasional IN ({in_clause(f_wilayah)})
          AND f.tahun_evaluasi BETWEEN ? AND ?
          AND p.nama_perusahaan LIKE ?
        ORDER BY f.total_skor_esg DESC
    """
    params = tuple(f_sektor) + tuple(f_wilayah) + (f_tahun[0], f_tahun[1], f"%{search_term}%")
    df_explore = run_query(explore_sql, params)

    st.caption(f"{len(df_explore):,} baris ditemukan".replace(",", "."))
    st.dataframe(df_explore, use_container_width=True, hide_index=True, height=440)

    st.download_button(
        "⬇️ Unduh hasil sebagai CSV",
        data=df_explore.to_csv(index=False).encode("utf-8"),
        file_name="eksplorasi_perusahaan_esg.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption("ESG Data Mart Project · Dashboard interaktif dibangun dengan Streamlit + Plotly · Muhammad Zidane Alhalita")
