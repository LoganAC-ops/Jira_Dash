import io
import json
import os
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
import streamlit as st

import jira_client

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ITEST Daily Status",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global styles — Mondelez / Accenture co-brand ────────────────────────────
st.markdown(
    """
    <style>
        /* ── Header ── */
        .main-header {
            background: linear-gradient(120deg, #1a0533 0%, #2d0b55 100%);
            padding: 0.5rem 1.4rem;
            border-radius: 6px;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #A100FF;
        }
        .header-left h1 {
            color: #ffffff;
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -.01em;
        }
        .header-left p {
            color: #c9a8f0;
            font-size: 0.72rem;
            margin: 0.15rem 0 0;
            letter-spacing: .02em;
        }
        .header-right {
            text-align: right;
            line-height: 1.6;
        }
        .brand-mdlz {
            display: block;
            color: #e8d5ff;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: .06em;
            text-transform: uppercase;
        }
        .brand-acc {
            display: block;
            color: #A100FF;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: .06em;
            text-transform: uppercase;
        }
        .brand-label {
            display: block;
            color: #9b72cf;
            font-size: 0.62rem;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-top: .1rem;
        }
        /* ── KPI tiles ── */
        .kpi-card {
            background: #ffffff;
            border: 1px solid #ede5f7;
            border-top: 4px solid #A100FF;
            border-radius: 8px;
            padding: 1.8rem 1.2rem;
            text-align: center;
            box-shadow: 0 2px 8px rgba(92,45,145,.10);
        }
        .kpi-label {
            font-size: 0.78rem;
            font-weight: 600;
            color: #7a5fa0;
            text-transform: uppercase;
            letter-spacing: .06em;
            margin-bottom: .6rem;
        }
        .kpi-value  { font-size: 3rem; font-weight: 700; line-height: 1; color: #5C2D91; }
        .kpi-purple { color: #5C2D91; }
        .kpi-red    { color: #5C2D91; }
        .kpi-amber  { color: #5C2D91; }
        .kpi-acc    { color: #5C2D91; }
        /* ── Section titles ── */
        .section-title {
            font-size: 1rem;
            font-weight: 600;
            color: #2d0b55;
            border-bottom: 2px solid #A100FF;
            padding-bottom: .3rem;
            margin-bottom: 1rem;
        }
        /* ── Priority breakdown table ── */
        .priority-table {
            width: 100%;
            border-collapse: collapse;
            font-family: sans-serif;
            margin-top: .5rem;
        }
        .priority-table th {
            background: #2d0b55;
            color: #e8d5ff;
            padding: .75rem 1.5rem;
            font-size: .85rem;
            font-weight: 600;
            letter-spacing: .06em;
            text-transform: uppercase;
        }
        .priority-table th:first-child { text-align: left; border-radius: 6px 0 0 0; }
        .priority-table th:last-child  { border-radius: 0 6px 0 0; }
        .priority-table th             { text-align: center; }
        .priority-table td {
            padding: .9rem 1.5rem;
            text-align: center;
            font-size: 1.2rem;
            font-weight: 600;
            border-bottom: 1px solid #ede5f7;
            background: #ffffff;
        }
        .priority-table td:first-child { text-align: left; }
        .priority-table tr:last-child td { border-bottom: none; }
        .priority-table tr:hover td { background: #f8f3ff; }
        .p-high   { color: #c62828; }
        .p-medium { color: #e65100; }
        .p-low    { color: #5C2D91; }
        /* ── Refresh button ── */
        div[data-testid="stButton"] button {
            background: linear-gradient(135deg, #A100FF 0%, #5C2D91 100%);
            color: #ffffff;
            border: none;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: .08em;
            text-transform: uppercase;
            box-shadow: 0 3px 10px rgba(161,0,255,.35);
            transition: box-shadow .15s, opacity .15s;
        }
        div[data-testid="stButton"] button:hover {
            opacity: 0.9;
            box-shadow: 0 5px 16px rgba(161,0,255,.5);
            border: none;
        }
        /* ── Hide Streamlit chrome ── */
        #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _kpi_html(label: str, value: int, css_class: str, subtitle: str = "") -> str:
    sub = (
        f'<div style="font-size:.72rem;color:#9b72cf;margin-top:.4rem">{subtitle}</div>'
        if subtitle else ""
    )
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {css_class}">{value}</div>
        {sub}
    </div>
    """


def _ordinal(d: date) -> str:
    n = d.day
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{d.strftime('%b')} {n}{suffix}"


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=300)
def load_data() -> pd.DataFrame:
    return jira_client.get_issues()


def refresh_data():
    st.cache_data.clear()
    st.session_state["last_refresh"] = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).strftime("%Y-%m-%d %H:%M CT")


if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).strftime("%Y-%m-%d %H:%M CT")

# ── Backlog snapshot (persist daily total for yesterday comparison) ────────────
_SNAPSHOT_FILE = os.path.join(os.path.dirname(__file__), "backlog_snapshot.json")

def _load_snapshot() -> dict:
    try:
        with open(_SNAPSHOT_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_snapshot(snapshot: dict):
    with open(_SNAPSHOT_FILE, "w") as f:
        json.dump(snapshot, f)

# ── Header ────────────────────────────────────────────────────────────────────
today_display = datetime.utcnow().strftime("%B %d, %Y")
st.markdown(
    f"""
    <div class="main-header">
        <div class="header-left">
            <h1>ITEST Daily Status &mdash; {today_display}</h1>
            <p>SAP S/4HANA Integration Testing &nbsp;&bull;&nbsp; Leadership Overview</p>
        </div>
        <div class="header-right">
            <span class="brand-mdlz">Mondelez International</span>
            <span class="brand-acc">Accenture</span>
            <span class="brand-label">Delivered together</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Pulling data from Jira…"):
    try:
        df = load_data()
    except EnvironmentError as exc:
        st.error(f"**Configuration error:** {exc}")
        st.stop()
    except RuntimeError as exc:
        st.error(f"**Jira API error:** {exc}")
        st.stop()

if df.empty:
    st.warning("No issues returned from Jira. Check your project key and permissions.")
    st.stop()

# ── Toolbar: refresh + filters ───────────────────────────────────────────────
col_refresh, col_region, col_org, col_status, col_status_mode = st.columns(
    [0.6, 1.5, 2.5, 2.5, 0.8], vertical_alignment="bottom"
)
with col_refresh:
    if st.button("Refresh", use_container_width=True, help=f"Last updated: {st.session_state['last_refresh']}"):
        refresh_data()

def _normalize_org(org: str) -> str:
    if isinstance(org, str) and org.lower().startswith("accenture"):
        return "Accenture"
    return org

df["responsible_org_display"] = df["responsible_org"].apply(_normalize_org)

with col_region:
    _region_opts = sorted(
        r for r in df["regions_impacted"].dropna().unique()
        if r and r != "Unassigned"
    )
    selected_regions = st.multiselect("Region", options=_region_opts, placeholder="All regions")
with col_org:
    all_orgs = sorted(df["responsible_org_display"].dropna().unique().tolist())
    selected_orgs = st.multiselect("Organization", options=all_orgs, placeholder="All organizations")
with col_status:
    all_statuses = sorted(df["status"].dropna().unique().tolist())
    selected_statuses = st.multiselect("Status", options=all_statuses, placeholder="All statuses")
with col_status_mode:
    status_exclude = st.toggle("Exclude", value=False, help="Exclude selected statuses instead of including them")
if selected_regions:
    df = df[df["regions_impacted"].apply(
        lambda r: any(sel in str(r).split(", ") for sel in selected_regions)
    )]
if selected_orgs:
    df = df[df["responsible_org_display"].isin(selected_orgs)]
if selected_statuses:
    if status_exclude:
        df = df[~df["status"].isin(selected_statuses)]
    else:
        df = df[df["status"].isin(selected_statuses)]

# ── Shared constants ──────────────────────────────────────────────────────────
RESOLVED_STATUSES = {"Closed", "Cancelled", "Rejected", "Deferred"}
today         = datetime.utcnow().date()
today_str     = today.strftime("%Y-%m-%d")
yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")

# ── Defect health data (shared across tabs) ───────────────────────────────────
open_df = df[df["is_active"]]

df_no_date      = open_df[open_df["planned_completion_date"].isna()]
df_overdue      = df[df["is_overdue"]]
df_cr           = df[df["defect_type"].str.contains("Change Request", na=False)]
df_retest       = df[df["status"] == "Retest"]
df_pending_info = df[df["status"] == "Pending Information"]
df_deferred     = df[df["status"] == "Deferred"]

n_no_date      = len(df_no_date)
n_overdue      = len(df_overdue)
n_cr           = len(df_cr)
n_retest       = len(df_retest)
n_pending_info = len(df_pending_info)
n_deferred     = len(df_deferred)

_DISP_COLS = {
    "issue_key":               "Key",
    "summary":                 "Summary",
    "workstream":              "Workstream",
    "status":                  "Status",
    "planned_completion_date": "Due Date",
}

def _defect_table(source_df):
    display = source_df[list(_DISP_COLS)].rename(columns=_DISP_COLS).copy()
    display["Summary"] = display["Summary"].str[:60]
    display = display.reset_index(drop=True)
    st.dataframe(display, use_container_width=True, hide_index=True)

health_specs_row1 = [
    ("No Completion Date", n_no_date, True,  "Open defects without a date", df_no_date),
    ("Overdue",            n_overdue, True,   "Past planned completion date", df_overdue),
    ("Change Requests",    n_cr,      False,  "Defect type: Change Request",  df_cr),
    ("In Retest",          n_retest,  False,  "Status: Retest",               df_retest),
]

health_specs_row2 = [
    ("Pending Information", n_pending_info, True,  "Status: Pending Information", df_pending_info),
    ("Deferred",            n_deferred,     True,  "Status: Deferred",            df_deferred),
]

def _health_widget(col, label, value, warn, subtitle, detail_df):
    num_color = "#c62828" if (warn and value > 0) else "#5C2D91"
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:0.9rem;font-weight:700;color:#2d0b55;text-transform:uppercase;
                        letter-spacing:.05em;margin-bottom:.6rem">{label}</div>
            <div class="kpi-value" style="color:{num_color}">{value}</div>
            <div style="font-size:.72rem;color:#9b72cf;margin-top:.4rem">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(f"View {value} defect{'s' if value != 1 else ''}"):
            if detail_df.empty:
                st.info("No defects in this category.")
            else:
                _defect_table(detail_df)

def _render_health_kpis():
    h1, h2, h3, h4 = st.columns(4)
    for col, spec in zip([h1, h2, h3, h4], health_specs_row1):
        _health_widget(col, *spec)
    st.markdown("<div style='margin-top:.75rem'></div>", unsafe_allow_html=True)
    r1, r2, _, _ = st.columns(4)
    for col, spec in zip([r1, r2], health_specs_row2):
        _health_widget(col, *spec)

# ── Aging defects data (shared across tabs) ───────────────────────────────────
_open_bugs = df[df["is_active"] & (df["issue_type"] == "Bug")].copy()
_open_bugs["bdays_open"] = _open_bugs["created_date"].apply(
    lambda d: int(np.busday_count(d, today.isoformat())) if d else 0
)

AGING_SPECS = [
    ("Critical", 1, "Critical open > 1 business day"),
    ("High",     2, "High open > 2 business days"),
    ("Medium",   4, "Medium open > 4 business days"),
    ("Low",      8, "Low open > 8 business days"),
]

aging_data = []
for sev, threshold, subtitle in AGING_SPECS:
    aged_df = _open_bugs[
        (_open_bugs["severity"] == sev) & (_open_bugs["bdays_open"] > threshold)
    ][["issue_key", "summary", "severity", "status", "bdays_open"]].copy()
    aged_df = aged_df.rename(columns={
        "issue_key":  "Key",
        "summary":    "Summary",
        "severity":   "Severity",
        "status":     "Status",
        "bdays_open": "Days Open",
    })
    aged_df["Summary"] = aged_df["Summary"].str[:60]
    aging_data.append((sev, threshold, subtitle, len(aged_df), aged_df))

def _render_aging_kpis():
    a1, a2, a3, a4 = st.columns(4)
    for col, (sev, threshold, subtitle, count, detail_df) in zip([a1, a2, a3, a4], aging_data):
        num_color = "#c62828" if count > 0 else "#5C2D91"
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div style="font-size:0.9rem;font-weight:700;color:#2d0b55;text-transform:uppercase;
                            letter-spacing:.05em;margin-bottom:.6rem">{sev}</div>
                <div class="kpi-value" style="color:{num_color}">{count}</div>
                <div style="font-size:.72rem;color:#9b72cf;margin-top:.4rem">{subtitle}</div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander(f"View {count} defect{'s' if count != 1 else ''}"):
                if detail_df.empty:
                    st.info("No aging defects in this category.")
                else:
                    st.dataframe(detail_df.reset_index(drop=True),
                                 use_container_width=True, hide_index=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
BPL1_MAP = {
    "RTR - Manage Finance":                                "Finance",
    "OTC":                                                 "OTC",
    "Data Governance/Manage Data":                         "Data",
    "LogOps":                                              "LogOps",
    "PTC-Plan to Cash":                                    "OTC",
    "STP-Source to Pay":                                   "STP",
    "MTI-Material to Inventory":                           "MTI",
    "Data & Analytics, Data Lakes & Information Management": "D&A",
    "Sell to Customer":                                    "Sales",
    "PLM - Product Lifecycle Management":                  "PLM",
    "Data Governanace":                                    "Data",
    "PTC-Plan to Cash - Credit Management":                "OTC",
    "IBP-Integrated Business Planning":                    "APO",
    "Materials to Inventory":                              "MTI",
    "Manage Information Technology and Solutions":         "Platform",
    "Unassigned":                                          "Unassigned",
}

# ── Pre-compute Deep Dive data (shared by tab3 and Excel export) ──────────────
_dd_base = df[df["is_active"] & (df["issue_type"] == "Bug")].copy()
_dd_base["days_open"] = _dd_base["created_date"].apply(
    lambda d: (today - date.fromisoformat(d)).days if d else 0
)
_dd_base["bdays_open"] = _dd_base["created_date"].apply(
    lambda d: int(np.busday_count(d, today.isoformat())) if d else 0
)
_dd_base["ws_group"] = _dd_base["business_process_l1"].map(BPL1_MAP).fillna("Unassigned")

_dd_ws_col = _dd_base["workstream"].fillna("")
_dd_sec    = _dd_base[_dd_base["workstream"].str.contains("SAP Security", na=False)]
_dd_int    = _dd_base[_dd_base["workstream"].str.contains("Integration", na=False, case=False)]
_dd_data   = _dd_base[
    (_dd_ws_col.str.lower() == "data") |
    (_dd_ws_col.str.lower().str.startswith("data -") & ~_dd_ws_col.str.lower().str.contains("data - signavio"))
]
_dd_other  = _dd_base[
    ~_dd_base["workstream"].str.contains("SAP Security", na=False) &
    ~_dd_base["workstream"].str.contains("Integration", na=False, case=False) &
    ~_dd_ws_col.str.lower().eq("data") &
    ~(_dd_ws_col.str.lower().str.startswith("data -") & ~_dd_ws_col.str.lower().str.contains("data - signavio"))
]


def _build_excel_report() -> bytes:
    _OV_COLS = {
        "issue_key": "Key", "summary": "Summary", "issue_type": "Issue Type",
        "status": "Status", "severity": "Severity", "priority": "Priority",
        "created_date": "Created Date", "planned_completion_date": "Due Date",
        "workstream": "Workstream", "responsible_org_display": "Organization",
        "regions_impacted": "Region",
    }
    _WS_COLS = {
        "issue_key": "Key", "summary": "Summary", "workstream": "Workstream",
        "status": "Status", "severity": "Severity",
        "planned_completion_date": "Due Date", "responsible_org_display": "Organization",
        "regions_impacted": "Region",
    }
    _DD_COLS = {
        "issue_key": "Key", "summary": "Summary", "ws_group": "Workstream Group",
        "workstream": "Workstream", "status": "Status", "severity": "Severity",
        "created_date": "Created Date", "bdays_open": "Business Days Open",
        "responsible_org_display": "Organization", "regions_impacted": "Region",
    }
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df[[c for c in _OV_COLS if c in df.columns]].rename(columns=_OV_COLS).to_excel(
            writer, sheet_name="Overview", index=False
        )
        open_df[[c for c in _WS_COLS if c in open_df.columns]].rename(columns=_WS_COLS).to_excel(
            writer, sheet_name="Workstream", index=False
        )
        _dd_base[[c for c in _DD_COLS if c in _dd_base.columns]].rename(columns=_DD_COLS).to_excel(
            writer, sheet_name="Deep Dive", index=False
        )
    buf.seek(0)
    return buf.getvalue()


# ── Excel download button ─────────────────────────────────────────────────────
_, _dl_col = st.columns([6, 2])
with _dl_col:
    st.download_button(
        label="Download Excel Report",
        data=_build_excel_report(),
        file_name=f"ITEST_Dashboard_{today_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

tab1, tab2, tab3 = st.tabs(["Overview", "Workstream", "Deep Dive"])

# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    # ── KPI tiles ─────────────────────────────────────────────────────────────
    n_new_today      = int(((df["created_date"] == today_str)    & (df["issue_type"] == "Bug")).sum())
    n_new_yest       = int(((df["created_date"] == yesterday_str) & (df["issue_type"] == "Bug")).sum())
    bugs = df["issue_type"] == "Bug"
    n_resolved       = int((bugs & df["status"].isin(RESOLVED_STATUSES)).sum())
    n_resolved_today = int((bugs & (df["created_date"] == today_str)     & df["status"].isin(RESOLVED_STATUSES)).sum())
    n_resolved_yest  = int((bugs & (df["created_date"] == yesterday_str) & df["status"].isin(RESOLVED_STATUSES)).sum())
    n_backlog        = int((bugs & ~df["status"].isin(RESOLVED_STATUSES)).sum())
    n_backlog_today  = int((bugs & (df["created_date"] == today_str)     & ~df["status"].isin(RESOLVED_STATUSES)).sum())
    n_backlog_yest   = int((bugs & (df["created_date"] == yesterday_str) & ~df["status"].isin(RESOLVED_STATUSES)).sum())

    # ── Persist today's total backlog; read yesterday's for arrow ─────────────
    _snapshot = _load_snapshot()
    _snapshot[today_str] = n_backlog
    _save_snapshot(_snapshot)
    n_backlog_yesterday_total = _snapshot.get(yesterday_str)

    yest_label = (today - timedelta(days=1)).strftime("%b %#d")

    def _arrow(today_val, yest_val, good="up"):
        if today_val == yest_val:
            return "●", "#9b72cf"
        going_up = today_val > yest_val
        symbol = "▲" if going_up else "▼"
        is_good = (good == "up") == going_up
        color  = "#2e7d32" if is_good else "#c62828"
        return symbol, color

    new_arrow,  new_color  = _arrow(n_new_today,      n_new_yest,      good="down")
    res_arrow,  res_color  = _arrow(n_resolved_today, n_resolved_yest, good="up")
    if n_backlog_yesterday_total is not None:
        bl_arrow, bl_color = _arrow(n_backlog, n_backlog_yesterday_total, good="down")
        bl_subtitle = f"{n_backlog_yesterday_total} yesterday ({yest_label})"
    else:
        bl_arrow, bl_color = "●", "#9b72cf"
        bl_subtitle = "No data from yesterday yet"

    kpi_left, kpi_mid, kpi_right = st.columns(3, gap="large")

    def _trend_card(label, big_value, big_css, arrow, arrow_color, subtitle):
        return f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div style="display:flex;justify-content:center;align-items:center;gap:0.6rem;margin:.6rem 0 .2rem">
                <div style="font-size:3rem;font-weight:700;{big_css};line-height:1">{big_value}</div>
                <div style="font-size:2.6rem;font-weight:700;color:{arrow_color};line-height:1">{arrow}</div>
            </div>
            <div style="font-size:.72rem;color:#9b72cf;margin-top:.3rem">{subtitle}</div>
        </div>
        """

    with kpi_left:
        st.markdown(_trend_card(
            f"New Defects — Today ({today.strftime('%b %#d')})",
            n_new_today, "color:#5C2D91",
            new_arrow, new_color,
            f"{n_new_yest} yesterday ({yest_label})"
        ), unsafe_allow_html=True)

    with kpi_mid:
        st.markdown(_trend_card(
            f"Resolved — Today ({today.strftime('%b %#d')})",
            n_resolved_today, "color:#5C2D91",
            res_arrow, res_color,
            f"{n_resolved_yest} yesterday ({yest_label})"
        ), unsafe_allow_html=True)

    with kpi_right:
        st.markdown(_trend_card(
            "Total Backlog",
            n_backlog, "color:#5C2D91",
            bl_arrow, bl_color,
            bl_subtitle
        ), unsafe_allow_html=True)

    # ── Priority breakdown ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    PRIORITY_ROWS = [
        ("Critical",   "p-low", "● Critical"),
        ("High",       "p-low", "● High"),
        ("Medium",     "p-low", "● Medium"),
        ("Low",        "p-low", "● Low"),
        ("Unassigned", "p-low", "● Unassigned"),
    ]

    KNOWN_SEVERITIES = {"Critical", "High", "Medium", "Low"}

    def _pcount(mask_a, severity):
        if severity == "Unassigned":
            return int((mask_a & ~df["severity"].isin(KNOWN_SEVERITIES)).sum())
        return int((mask_a & (df["severity"] == severity)).sum())

    mask_new      = (df["created_date"] == today_str) & bugs
    mask_resolved = (df["created_date"] == today_str) & bugs & df["status"].isin(RESOLVED_STATUSES)
    mask_backlog  = bugs & ~df["status"].isin(RESOLVED_STATUSES)

    rows_html = ""
    for priority, css, label in PRIORITY_ROWS:
        rows_html += f"""
            <tr>
                <td><span class="{css}">{label}</span></td>
                <td>{_pcount(mask_new, priority)}</td>
                <td>{_pcount(mask_resolved, priority)}</td>
                <td>{_pcount(mask_backlog, priority)}</td>
            </tr>"""

    with st.container():
        st.markdown(
            f"""
            <table class="priority-table">
                <thead>
                    <tr>
                        <th>Severity</th>
                        <th>New Defects</th>
                        <th>Resolved</th>
                        <th>Backlog</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Defect Health</div>', unsafe_allow_html=True)
    _render_health_kpis()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Aging Defects by Severity</div>', unsafe_allow_html=True)
    _render_aging_kpis()

# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    # ── Planned completions section ───────────────────────────────────────────
    st.markdown('<div class="section-title">Planned Completions</div>', unsafe_allow_html=True)

    ws_options = sorted(
        open_df.loc[open_df["workstream"] != "Unassigned", "workstream"].dropna().unique().tolist()
    )
    sel_ws = st.multiselect("Filter by Workstream", ws_options, placeholder="All workstreams", key="ws_filter")
    ws_df = open_df if not sel_ws else open_df[open_df["workstream"].isin(sel_ws)]

    def _next_bdays(start: date, n: int):
        days, d = [], start
        while len(days) < n:
            if d.weekday() < 5:
                days.append(d)
            d += timedelta(days=1)
        return days

    # 4 date KPI widgets — next 4 business days
    bdays_4 = _next_bdays(today, 4)
    d_cols = st.columns(4)
    for i, (col, d) in enumerate(zip(d_cols, bdays_4)):
        day_label  = "Today" if i == 0 else d.strftime("%A")
        date_label = d.strftime("%b %d")
        count = int((ws_df["planned_completion_date"] == d).sum())
        with col:
            st.markdown(_kpi_html(day_label, count, "kpi-purple", date_label), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Open defects grouped by date & workstream ─────────────────────────────
    # ── Open defects grouped by date & workstream ─────────────────────────────
    st.markdown('<div class="section-title">Open Defects by Planned Date &amp; Workstream</div>', unsafe_allow_html=True)

    upcoming_bdays = _next_bdays(today, 5)
    range_df = open_df[open_df["planned_completion_date"].isin(upcoming_bdays)]

    if range_df.empty:
        st.info("No open defects with planned completion dates in the next 5 business days.")
    else:
        sorted_dates = sorted(range_df["planned_completion_date"].unique())

        for d in sorted_dates:
            day_df = range_df[range_df["planned_completion_date"] == d]
            ws_counts = day_df.groupby("workstream").size().sort_values(ascending=False).head(5)
            total = int(len(day_df))
            badges = "".join(
                f"<span style='background:#f3e8ff;color:#5C2D91;padding:.3rem .9rem;"
                f"border-radius:20px;font-size:.95rem;font-weight:600;white-space:nowrap'>"
                f"{ws}&nbsp;<strong style='color:#5C2D91'>{int(cnt)}</strong></span>"
                for ws, cnt in ws_counts.items()
            )
            st.markdown(
                f"<div style='background:#fff;border:1px solid #ede5f7;border-left:4px solid #A100FF;"
                f"border-radius:6px;padding:.8rem 1.2rem;margin-bottom:.5rem;"
                f"display:flex;align-items:center;gap:1.2rem;flex-wrap:wrap'>"
                f"<div style='min-width:90px'>"
                f"<div style='font-weight:700;color:#2d0b55;font-size:1.05rem'>{_ordinal(d)}</div>"
                f"<div style='font-size:.72rem;color:#9b72cf;margin-top:.1rem'>{d.strftime('%A')}</div>"
                f"</div>"
                f"<div style='color:#9b72cf;font-size:.85rem;min-width:55px'>{total} total</div>"
                f"<div style='display:flex;flex-wrap:wrap;gap:.5rem'>{badges}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Completion date distribution ──────────────────────────────────────────
    st.markdown('<div class="section-title">Defects by Days Until Planned Completion</div>', unsafe_allow_html=True)

    BUCKETS = [
        ("25+ days",   25, 9999),
        ("20–24 days", 20, 24),
        ("15–19 days", 15, 19),
        ("10–14 days", 10, 14),
        ("5–9 days",   5,  9),
        ("0–4 days",   0,  4),
    ]

    sched_df = ws_df[ws_df["planned_completion_date"].notna()].copy()
    sched_df["days_until"] = sched_df["planned_completion_date"].apply(lambda d: (d - today).days)
    sched_df = sched_df[sched_df["days_until"] >= 0]

    _BUCKET_COLS = {"issue_key": "Key", "summary": "Summary", "status": "Status",
                    "planned_completion_date": "Due Date", "workstream": "Workstream"}

    bucket_data = []
    for label, lo, hi in BUCKETS:
        mask = (sched_df["days_until"] >= lo) & (sched_df["days_until"] <= hi)
        detail = sched_df[mask][list(_BUCKET_COLS)].rename(columns=_BUCKET_COLS).copy()
        detail["Summary"] = detail["Summary"].str[:60]
        bucket_data.append((label, len(detail), detail))

    cols = st.columns(6)
    for col, (label, cnt, detail) in zip(cols, bucket_data):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="padding:1rem .6rem">
                <div style="font-size:.75rem;font-weight:600;color:#7a5fa0;text-transform:uppercase;
                            letter-spacing:.05em;margin-bottom:.5rem">{label}</div>
                <div class="kpi-value" style="font-size:2rem;color:#5C2D91">{cnt}</div>
            </div>""", unsafe_allow_html=True)
            with st.expander(label):
                if detail.empty:
                    st.info("No defects.")
                else:
                    st.dataframe(detail.reset_index(drop=True), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
def _build_totals_table(sec_df: pd.DataFrame, int_df: pd.DataFrame, data_df: pd.DataFrame, func_df: pd.DataFrame) -> str:
    WS_ORDER = ["Finance", "OTC", "Data", "LogOps", "STP", "MTI", "D&A",
                "Sales", "PLM", "APO", "Platform", "Unassigned"]

    th_style = ("background:#2d0b55;color:#e8d5ff;padding:0.4rem 0.75rem;font-size:1rem;"
                "font-weight:700;letter-spacing:.04em;text-align:center;white-space:nowrap")
    th_left  = ("background:#2d0b55;color:#e8d5ff;padding:0.4rem 0.75rem;font-size:1rem;"
                "font-weight:700;letter-spacing:.04em;text-align:left;white-space:nowrap")
    td_num   = ("padding:0.3rem 0.75rem;text-align:center;font-size:1.2rem;"
                "font-weight:700;color:#5C2D91;border-bottom:1px solid #ede5f7")
    td_grand = ("padding:0.3rem 0.75rem;text-align:center;font-size:1.2rem;"
                "font-weight:700;color:#2d0b55;border-bottom:1px solid #ede5f7;"
                "border-left:2px solid #ede5f7")
    td_ws    = ("padding:0.3rem 0.75rem;font-weight:700;color:#2d0b55;font-size:1rem;"
                "border-bottom:1px solid #ede5f7;white-space:nowrap")
    td_foot  = ("padding:0.4rem 0.75rem;text-align:center;font-size:1.2rem;"
                "font-weight:700;color:#fff;background:#3d1a6e;border-top:2px solid #3d1a6e")
    td_foot_grand = ("padding:0.4rem 0.75rem;text-align:center;font-size:1.2rem;"
                     "font-weight:700;color:#fff;background:#2d0b55;border-top:2px solid #3d1a6e;"
                     "border-left:2px solid #5c2d91")
    td_foot_ws = ("padding:0.4rem 0.75rem;font-weight:700;color:#fff;font-size:1rem;"
                  "background:#3d1a6e;border-top:2px solid #3d1a6e;white-space:nowrap")

    header = (
        f"<th style='{th_style}'>Security</th>"
        f"<th style='{th_style}'>Integration</th>"
        f"<th style='{th_style}'>Data</th>"
        f"<th style='{th_style}'>Functional</th>"
        f"<th style='{th_style};border-left:2px solid #3d1a6e'>Total</th>"
    )

    rows_html = ""
    col_totals = [0, 0, 0, 0]
    grand_total = 0
    for ws in WS_ORDER:
        n_sec  = int((sec_df["ws_group"]  == ws).sum())
        n_int  = int((int_df["ws_group"]  == ws).sum())
        n_dat  = int((data_df["ws_group"] == ws).sum())
        n_func = int((func_df["ws_group"] == ws).sum())
        total  = n_sec + n_int + n_dat + n_func
        if total == 0:
            continue
        col_totals[0] += n_sec
        col_totals[1] += n_int
        col_totals[2] += n_dat
        col_totals[3] += n_func
        grand_total   += total
        rows_html += (
            f"<tr>"
            f"<td style='{td_ws}'>{ws}</td>"
            f"<td style='{td_num}'>{n_sec}</td>"
            f"<td style='{td_num}'>{n_int}</td>"
            f"<td style='{td_num}'>{n_dat}</td>"
            f"<td style='{td_num}'>{n_func}</td>"
            f"<td style='{td_grand}'>{total}</td>"
            f"</tr>"
        )

    rows_html += (
        f"<tr>"
        f"<td style='{td_foot_ws}'>Total</td>"
        f"<td style='{td_foot}'>{col_totals[0]}</td>"
        f"<td style='{td_foot}'>{col_totals[1]}</td>"
        f"<td style='{td_foot}'>{col_totals[2]}</td>"
        f"<td style='{td_foot}'>{col_totals[3]}</td>"
        f"<td style='{td_foot_grand}'>{grand_total}</td>"
        f"</tr>"
    )

    return (
        f"<div style='border:1px solid #ede5f7;border-radius:8px;overflow:hidden;margin-top:.5rem'>"
        f"<table style='border-collapse:collapse;width:100%;table-layout:fixed'>"
        f"<thead><tr><th style='{th_left}'>Workstream</th>{header}</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        f"</table></div>"
    )


def _build_age_table(filtered_df: pd.DataFrame, today: date) -> str:
    WS_ORDER = ["Finance", "OTC", "Data", "LogOps", "STP", "MTI", "D&A",
                "Sales", "PLM", "APO", "Platform", "Unassigned"]
    DAY_COLS = [("4+ Days", lambda x: x >= 4),
                ("3 Days",  lambda x: x == 3),
                ("2 Days",  lambda x: x == 2),
                ("1 Day",   lambda x: x == 1),
                ("Today",   lambda x: x == 0)]

    th_style = ("background:#2d0b55;color:#e8d5ff;padding:0.4rem 0.75rem;font-size:1rem;"
                "font-weight:700;letter-spacing:.04em;text-align:center;white-space:nowrap")
    th_left  = ("background:#2d0b55;color:#e8d5ff;padding:0.4rem 0.75rem;font-size:1rem;"
                "font-weight:700;letter-spacing:.04em;text-align:left;white-space:nowrap")
    td_num   = ("padding:0.3rem 0.75rem;text-align:center;font-size:1.2rem;"
                "font-weight:700;color:#5C2D91;border-bottom:1px solid #ede5f7")
    td_total = ("padding:0.3rem 0.75rem;text-align:center;font-size:1.2rem;"
                "font-weight:700;color:#2d0b55;border-bottom:1px solid #ede5f7;"
                "border-left:2px solid #ede5f7")
    td_ws    = ("padding:0.3rem 0.75rem;font-weight:700;color:#2d0b55;font-size:1rem;"
                "border-bottom:1px solid #ede5f7;white-space:nowrap")
    td_foot  = ("padding:0.4rem 0.75rem;text-align:center;font-size:1.2rem;"
                "font-weight:700;color:#fff;background:#3d1a6e;border-top:2px solid #3d1a6e")
    td_foot_total = ("padding:0.4rem 0.75rem;text-align:center;font-size:1.2rem;"
                     "font-weight:700;color:#fff;background:#2d0b55;border-top:2px solid #3d1a6e;"
                     "border-left:2px solid #5c2d91")
    td_foot_ws = ("padding:0.4rem 0.75rem;font-weight:700;color:#fff;font-size:1rem;"
                  "background:#3d1a6e;border-top:2px solid #3d1a6e;white-space:nowrap")

    header_cells = "".join(f"<th style='{th_style}'>{col}</th>" for col, _ in DAY_COLS)
    header_cells += f"<th style='{th_style};border-left:2px solid #3d1a6e'>Total</th>"

    rows_html = ""
    col_totals = [0] * len(DAY_COLS)
    grand_total = 0
    for ws in WS_ORDER:
        ws_bugs = filtered_df[filtered_df["ws_group"] == ws]
        counts = [int(fn(ws_bugs["days_open"]).sum()) if not ws_bugs.empty else 0 for _, fn in DAY_COLS]
        total  = int(len(ws_bugs)) if not ws_bugs.empty else 0
        if total == 0:
            continue
        for i, c in enumerate(counts):
            col_totals[i] += c
        grand_total += total
        cells = "".join(f"<td style='{td_num}'>{c}</td>" for c in counts)
        rows_html += (
            f"<tr><td style='{td_ws}'>{ws}</td>{cells}"
            f"<td style='{td_total}'>{total}</td></tr>"
        )

    footer_cells = "".join(f"<td style='{td_foot}'>{c}</td>" for c in col_totals)
    footer_cells += f"<td style='{td_foot_total}'>{grand_total}</td>"
    rows_html += f"<tr><td style='{td_foot_ws}'>Total</td>{footer_cells}</tr>"

    return (
        f"<div style='border:1px solid #ede5f7;border-radius:8px;overflow:hidden;"
        f"margin-top:.5rem'>"
        f"<table style='border-collapse:collapse;width:100%;table-layout:fixed'>"
        f"<thead><tr><th style='{th_left}'>Workstream</th>{header_cells}</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        f"</table></div>"
    )


with tab3:
    col_sec, col_int = st.columns(2, gap="medium")

    with col_sec:
        st.markdown('<div class="section-title">SAP Security — Open Defects by Workstream &amp; Age</div>', unsafe_allow_html=True)
        st.markdown(_build_age_table(_dd_sec, today), unsafe_allow_html=True)

    with col_int:
        st.markdown('<div class="section-title">Integration — Open Defects by Workstream &amp; Age</div>', unsafe_allow_html=True)
        st.markdown(_build_age_table(_dd_int, today), unsafe_allow_html=True)

    col_func, col_data = st.columns(2, gap="medium")

    with col_func:
        st.markdown('<div class="section-title" style="margin-top:1.5rem">Functional — Open Defects by Workstream &amp; Age</div>', unsafe_allow_html=True)
        st.markdown(_build_age_table(_dd_other, today), unsafe_allow_html=True)

    with col_data:
        st.markdown('<div class="section-title" style="margin-top:1.5rem">Data — Open Defects by Workstream &amp; Age</div>', unsafe_allow_html=True)
        st.markdown(_build_age_table(_dd_data, today), unsafe_allow_html=True)

    st.markdown('<div class="section-title" style="margin-top:1.5rem">Totals — Open Defects by Workstream</div>', unsafe_allow_html=True)
    st.markdown(_build_totals_table(_dd_sec, _dd_int, _dd_data, _dd_other), unsafe_allow_html=True)
