#!/usr/bin/env python3
"""
Menghasilkan diagram ERD (star schema / fact constellation) untuk
ESG Data Mart dalam format PNG & SVG, disimpan ke docs/erd_diagram.*

Penulis: Muhammad Zidane Alhalita
"""
from pathlib import Path
import graphviz

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "docs"
OUT_DIR.mkdir(exist_ok=True)

g = graphviz.Digraph("ESG_Data_Mart_ERD", format="png")
g.attr(
    rankdir="LR",
    bgcolor="white",
    fontname="Helvetica",
    labelloc="t",
    label="ESG Data Mart — Star Schema (Fact Constellation)\nMuhammad Zidane Alhalita",
    fontsize="18",
    pad="0.4",
)
g.attr("node", shape="plaintext", fontname="Helvetica")
g.attr("edge", fontname="Helvetica", fontsize="10", color="#5b6b73")

FACT_COLOR = "#F4A259"
DIM_COLOR = "#5B8DB8"
DERIVED_DIM_COLOR = "#8AA399"
HEADER_TEXT = "white"


def table_html(title, rows, header_color, subtitle=None):
    sub = f'<FONT POINT-SIZE="10"><I>{subtitle}</I></FONT><BR/>' if subtitle else ""
    row_html = ""
    for col_name, col_type, key in rows:
        key_badge = ""
        if key == "PK":
            key_badge = '<FONT COLOR="#B23A48"><B>PK</B></FONT> '
        elif key == "FK":
            key_badge = '<FONT COLOR="#3A6EA5"><B>FK</B></FONT> '
        row_html += (
            f'<TR><TD ALIGN="LEFT" CELLPADDING="4">{key_badge}{col_name}</TD>'
            f'<TD ALIGN="LEFT" CELLPADDING="4"><FONT COLOR="#666666">{col_type}</FONT></TD></TR>'
        )
    return f"""<
<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" COLOR="#CCCCCC">
  <TR><TD COLSPAN="2" BGCOLOR="{header_color}" CELLPADDING="6"><FONT COLOR="{HEADER_TEXT}"><B>{title}</B></FONT><BR/>{sub}</TD></TR>
  {row_html}
</TABLE>>"""


# ---------------------------------------------------------------------
# DIMENSI
# ---------------------------------------------------------------------
g.node(
    "dim_perusahaan",
    table_html(
        "dim_perusahaan",
        [
            ("company_id", "TEXT", "PK"),
            ("nama_perusahaan", "TEXT", ""),
            ("sektor", "TEXT", ""),
            ("wilayah_operasional", "TEXT", ""),
            ("tahun_listing", "INTEGER", ""),
        ],
        DIM_COLOR,
        "Sumber: dim_perusahaan.csv",
    ),
)

g.node(
    "dim_metrik_esg",
    table_html(
        "dim_metrik_esg",
        [
            ("metric_id", "TEXT", "PK"),
            ("pilar", "TEXT", ""),
            ("nama_metrik", "TEXT", ""),
            ("satuan", "TEXT", ""),
            ("target_kepatuhan_persen", "REAL", ""),
        ],
        DIM_COLOR,
        "Sumber: dim_metrik_esg.csv",
    ),
)

g.node(
    "dim_waktu_bulan",
    table_html(
        "dim_waktu_bulan",
        [
            ("bulan", "INTEGER", "PK"),
            ("nama_bulan", "TEXT", ""),
            ("nama_bulan_singkat", "TEXT", ""),
            ("kuartal", "TEXT", ""),
            ("semester", "TEXT", ""),
        ],
        DERIVED_DIM_COLOR,
        "Dimensi turunan (dibangun oleh ETL)",
    ),
)

g.node(
    "dim_peringkat_esg",
    table_html(
        "dim_peringkat_esg",
        [
            ("peringkat_esg", "TEXT", "PK"),
            ("urutan_peringkat", "INTEGER", ""),
            ("kategori_risiko", "TEXT", ""),
            ("deskripsi", "TEXT", ""),
        ],
        DERIVED_DIM_COLOR,
        "Dimensi turunan (dibangun oleh ETL)",
    ),
)

# ---------------------------------------------------------------------
# FAKTA
# ---------------------------------------------------------------------
g.node(
    "fact_penilaian_tahunan",
    table_html(
        "fact_penilaian_tahunan",
        [
            ("fact_score_id", "TEXT", "PK"),
            ("company_id", "TEXT", "FK"),
            ("tahun_evaluasi", "INTEGER", ""),
            ("skor_environmental", "INTEGER", ""),
            ("skor_social", "INTEGER", ""),
            ("skor_governance", "INTEGER", ""),
            ("total_skor_esg", "REAL", ""),
            ("peringkat_esg", "TEXT", "FK"),
        ],
        FACT_COLOR,
        "Grain: 1 baris = 1 perusahaan x 1 tahun evaluasi",
    ),
)

g.node(
    "fact_catatan_aktivitas",
    table_html(
        "fact_catatan_aktivitas",
        [
            ("fact_activity_id", "TEXT", "PK"),
            ("company_id", "TEXT", "FK"),
            ("metric_id", "TEXT", "FK"),
            ("bulan", "INTEGER", "FK"),
            ("nilai_realisasi", "REAL", ""),
            ("status_kepatuhan", "TEXT", ""),
            ("biaya_mitigasi_idr", "INTEGER", ""),
        ],
        FACT_COLOR,
        "Grain: 1 baris = 1 metrik x 1 perusahaan x 1 bulan",
    ),
)

# ---------------------------------------------------------------------
# RELASI
# ---------------------------------------------------------------------
g.edge("dim_perusahaan", "fact_penilaian_tahunan", label="1 : N", dir="back", arrowtail="crow")
g.edge("dim_peringkat_esg", "fact_penilaian_tahunan", label="1 : N", dir="back", arrowtail="crow")
g.edge("dim_perusahaan", "fact_catatan_aktivitas", label="1 : N", dir="back", arrowtail="crow")
g.edge("dim_metrik_esg", "fact_catatan_aktivitas", label="1 : N", dir="back", arrowtail="crow")
g.edge("dim_waktu_bulan", "fact_catatan_aktivitas", label="1 : N", dir="back", arrowtail="crow")

# Render
png_path = g.render(filename="erd_diagram", directory=str(OUT_DIR), cleanup=True)
print("ERD PNG generated at:", png_path)

g.format = "svg"
svg_path = g.render(filename="erd_diagram", directory=str(OUT_DIR), cleanup=True)
print("ERD SVG generated at:", svg_path)
