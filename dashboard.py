from datetime import date, datetime, timedelta

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
        .kpi-value  { font-size: 3rem; font-weight: 700; line-height: 1; }
        .kpi-purple { color: #5C2D91; }
        .kpi-red    { color: #c62828; }
        .kpi-amber  { color: #e65100; }
        .kpi-acc    { color: #A100FF; }
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
    st.session_state["last_refresh"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

# ── Toolbar: refresh + org filter ────────────────────────────────────────────
col_refresh, col_meta, col_org = st.columns([1, 3, 3], vertical_alignment="bottom")
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_data()
with col_meta:
    st.caption(f"{len(df)} issues loaded · Last refreshed: {st.session_state['last_refresh']}")
with col_org:
    all_orgs = sorted(df["responsible_org"].dropna().unique().tolist())
    selected_orgs = st.multiselect("Responsible Organization", options=all_orgs, placeholder="All organizations")
if selected_orgs:
    df = df[df["responsible_org"].isin(selected_orgs)]

# ── Shared constants ──────────────────────────────────────────────────────────
RESOLVED_STATUSES = {"Closed", "Cancelled", "Rejected", "Deferred"}
today = datetime.utcnow().date()
yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Overview", "Workstream"])

# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    # ── KPI tiles ─────────────────────────────────────────────────────────────
    today_str      = today.strftime("%Y-%m-%d")
    n_new_today      = int(((df["created_date"] == today_str)    & (df["issue_type"] == "Bug")).sum())
    n_new_yest       = int(((df["created_date"] == yesterday_str) & (df["issue_type"] == "Bug")).sum())
    bugs = df["issue_type"] == "Bug"
    n_resolved       = int((bugs & df["status"].isin(RESOLVED_STATUSES)).sum())
    n_resolved_today = int((bugs & (df["created_date"] == today_str)     & df["status"].isin(RESOLVED_STATUSES)).sum())
    n_resolved_yest  = int((bugs & (df["created_date"] == yesterday_str) & df["status"].isin(RESOLVED_STATUSES)).sum())
    n_backlog        = int((bugs & ~df["status"].isin(RESOLVED_STATUSES)).sum())
    n_backlog_today  = int((bugs & (df["created_date"] == today_str)     & ~df["status"].isin(RESOLVED_STATUSES)).sum())
    n_backlog_yest   = int((bugs & (df["created_date"] == yesterday_str) & ~df["status"].isin(RESOLVED_STATUSES)).sum())

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
    bl_arrow,   bl_color   = _arrow(n_backlog_today,  n_backlog_yest,  good="down")

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
            n_new_today, "color:#e65100",
            new_arrow, new_color,
            f"{n_new_yest} yesterday ({yest_label})"
        ), unsafe_allow_html=True)

    with kpi_mid:
        st.markdown(_trend_card(
            f"Resolved — Today ({today.strftime('%b %#d')})",
            n_resolved_today, "color:#5C2D91",
            res_arrow, res_color,
            f"{n_resolved_yest} yesterday ({yest_label}) · {n_resolved} total"
        ), unsafe_allow_html=True)

    with kpi_right:
        st.markdown(_kpi_html(
            "Total Backlog",
            n_backlog, "kpi-acc",
            "Open bugs"
        ), unsafe_allow_html=True)

    # ── Priority breakdown ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    PRIORITY_ROWS = [
        ("High",   "p-high",   "● High"),
        ("Medium", "p-medium", "● Medium"),
        ("Low",    "p-low",    "● Low"),
    ]

    def _pcount(mask_a, severity):
        return int((mask_a & (df["severity"] == severity)).sum())

    mask_new      = (df["created_date"] == today_str) & (df["issue_type"] == "Bug")
    mask_resolved = (df["created_date"] == today_str) & bugs & df["status"].isin(RESOLVED_STATUSES)
    mask_backlog  = (df["created_date"] == today_str) & bugs & ~df["status"].isin(RESOLVED_STATUSES)

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

# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    open_df = df[df["is_active"]]

    # ── Defect health KPIs ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Defect Health</div>', unsafe_allow_html=True)

    df_no_date = open_df[open_df["planned_completion_date"].isna()]
    df_overdue = df[df["is_overdue"]]
    df_cr      = df[df["defect_type"].str.contains("Change Request", na=False)]
    df_retest  = df[df["status"] == "Retest"]

    n_no_date = len(df_no_date)
    n_overdue = len(df_overdue)
    n_cr      = len(df_cr)
    n_retest  = len(df_retest)

    _DISP_COLS = {
        "issue_key":              "Key",
        "summary":                "Summary",
        "workstream":             "Workstream",
        "status":                 "Status",
        "planned_completion_date":"Due Date",
    }

    def _defect_table(source_df):
        display = source_df[list(_DISP_COLS)].rename(columns=_DISP_COLS).copy()
        display["Summary"] = display["Summary"].str[:60]
        display = display.reset_index(drop=True)
        st.dataframe(display, use_container_width=True, hide_index=True)

    health_specs = [
        ("No Completion Date", n_no_date, "kpi-amber",  "Open defects without a date",      df_no_date),
        ("Overdue",            n_overdue, "kpi-red",    "Past planned completion date",      df_overdue),
        ("Change Requests",    n_cr,      "kpi-purple", "Defect type: Change Request",       df_cr),
        ("In Retest",          n_retest,  "kpi-acc",    "Status: Retest",                    df_retest),
    ]

    h1, h2, h3, h4 = st.columns(4)
    for col, (label, value, css, subtitle, detail_df) in zip([h1, h2, h3, h4], health_specs):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div style="font-size:0.9rem;font-weight:700;color:#2d0b55;text-transform:uppercase;
                            letter-spacing:.05em;margin-bottom:.6rem">{label}</div>
                <div class="kpi-value {css}">{value}</div>
                <div style="font-size:.72rem;color:#9b72cf;margin-top:.4rem">{subtitle}</div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander(f"View {value} defect{'s' if value != 1 else ''}"):
                if detail_df.empty:
                    st.info("No defects in this category.")
                else:
                    _defect_table(detail_df)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Planned completions section ───────────────────────────────────────────
    st.markdown('<div class="section-title">Planned Completions</div>', unsafe_allow_html=True)

    ws_options = ["All"] + sorted(
        open_df.loc[open_df["workstream"] != "Unassigned", "workstream"].dropna().unique().tolist()
    )
    sel_ws = st.selectbox("Filter by Workstream", ws_options, key="ws_filter")
    ws_df = open_df if sel_ws == "All" else open_df[open_df["workstream"] == sel_ws]

    # 4 date KPI widgets — today through today+3
    d_cols = st.columns(4)
    for i, col in enumerate(d_cols):
        d = today + timedelta(days=i)
        day_label  = "Today" if i == 0 else d.strftime("%A")
        date_label = d.strftime("%b %d")
        count = int((ws_df["planned_completion_date"] == d).sum())
        with col:
            st.markdown(_kpi_html(day_label, count, "kpi-purple", date_label), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Open defects grouped by date & workstream ─────────────────────────────
    st.markdown('<div class="section-title">Open Defects by Planned Date &amp; Workstream</div>', unsafe_allow_html=True)

    upcoming_5 = [today + timedelta(days=i) for i in range(6)]
    range_df = ws_df[ws_df["planned_completion_date"].isin(upcoming_5)]

    if range_df.empty:
        st.info("No open defects with planned completion dates in the next 5 days.")
    else:
        sorted_dates = sorted(range_df["planned_completion_date"].unique())

        for d in sorted_dates:
            day_df = range_df[range_df["planned_completion_date"] == d]
            ws_counts = day_df.groupby("workstream").size().sort_values(ascending=False).head(5)
            total = int(len(day_df))
            badges = "".join(
                f"<span style='background:#f3e8ff;color:#5C2D91;padding:.3rem .9rem;"
                f"border-radius:20px;font-size:.95rem;font-weight:600;white-space:nowrap'>"
                f"{ws}&nbsp;<strong style='color:#A100FF'>{int(cnt)}</strong></span>"
                for ws, cnt in ws_counts.items()
            )
            st.markdown(
                f"<div style='background:#fff;border:1px solid #ede5f7;border-left:4px solid #A100FF;"
                f"border-radius:6px;padding:.8rem 1.2rem;margin-bottom:.5rem;"
                f"display:flex;align-items:center;gap:1.2rem;flex-wrap:wrap'>"
                f"<div style='font-weight:700;color:#2d0b55;font-size:1.05rem;min-width:80px'>{_ordinal(d)}</div>"
                f"<div style='color:#9b72cf;font-size:.85rem;min-width:55px'>{total} total</div>"
                f"<div style='display:flex;flex-wrap:wrap;gap:.5rem'>{badges}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
