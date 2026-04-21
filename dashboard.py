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
            padding: 0.85rem 1.6rem;
            border-radius: 8px;
            margin-bottom: 0.6rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 5px solid #A100FF;
        }
        .header-left h1 {
            color: #ffffff;
            font-size: 1.55rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -.01em;
        }
        .header-left p {
            color: #c9a8f0;
            font-size: 0.82rem;
            margin: 0.35rem 0 0;
            letter-spacing: .02em;
        }
        .header-right {
            text-align: right;
            line-height: 1.6;
        }
        .brand-mdlz {
            display: block;
            color: #e8d5ff;
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: .06em;
            text-transform: uppercase;
        }
        .brand-acc {
            display: block;
            color: #A100FF;
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: .06em;
            text-transform: uppercase;
        }
        .brand-label {
            display: block;
            color: #9b72cf;
            font-size: 0.68rem;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-top: .15rem;
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
            padding: .55rem 1.2rem;
            font-size: .75rem;
            font-weight: 600;
            letter-spacing: .06em;
            text-transform: uppercase;
        }
        .priority-table th:first-child { text-align: left; border-radius: 6px 0 0 0; }
        .priority-table th:last-child  { border-radius: 0 6px 0 0; }
        .priority-table th             { text-align: center; }
        .priority-table td {
            padding: .6rem 1.2rem;
            text-align: center;
            font-size: 1rem;
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
today_display = date.today().strftime("%B %d, %Y")
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
col_refresh, col_ts, col_org = st.columns([1, 2, 3], vertical_alignment="bottom")
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        refresh_data()
with col_ts:
    st.caption(f"Last refreshed: {st.session_state['last_refresh']}")
with col_org:
    all_orgs = ["All"] + sorted(df["responsible_org"].dropna().unique().tolist())
    selected_org = st.selectbox("Responsible Organization", options=all_orgs)
if selected_org != "All":
    df = df[df["responsible_org"] == selected_org]

st.caption(f"🔍 DEBUG — {len(df)} issues loaded")
with st.expander("🔍 DEBUG — field values"):
    st.write("Statuses:", sorted(df["status"].unique().tolist()))
    st.write("Issue types:", sorted(df["issue_type"].unique().tolist()))
    st.write("Stage found:", sorted(df["stage_found"].unique().tolist()))

# ── Shared constants ──────────────────────────────────────────────────────────
RESOLVED_STATUSES = {"Closed", "Cancelled", "Rejected", "Deferred"}
yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
today = date.today()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Overview", "Workstream"])

# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    # ── KPI tiles ─────────────────────────────────────────────────────────────
    today_str      = today.strftime("%Y-%m-%d")
    n_new_today    = int(((df["created_date"] == today_str)    & (df["issue_type"] == "Bug")).sum())
    n_new_yest     = int(((df["created_date"] == yesterday_str) & (df["issue_type"] == "Bug")).sum())
    n_resolved     = int(df["status"].isin(RESOLVED_STATUSES).sum())
    n_backlog      = int((~df["status"].isin(RESOLVED_STATUSES)).sum())

    today_label     = today.strftime("%b %#d")
    yest_label      = (today - timedelta(days=1)).strftime("%b %#d")

    kpi_left, kpi_mid, kpi_right = st.columns(3, gap="large")

    with kpi_left:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">New Defects</div>
            <div style="display:flex;justify-content:space-around;align-items:center;margin:.6rem 0 .2rem">
                <div style="text-align:center">
                    <div style="font-size:2.4rem;font-weight:700;color:#e65100;line-height:1">{n_new_yest}</div>
                    <div style="font-size:.72rem;color:#9b72cf;margin-top:.3rem">{yest_label} · Yesterday</div>
                </div>
                <div style="width:1px;height:3rem;background:#ede5f7"></div>
                <div style="text-align:center">
                    <div style="font-size:2.4rem;font-weight:700;color:#e65100;line-height:1">{n_new_today}</div>
                    <div style="font-size:.72rem;color:#9b72cf;margin-top:.3rem">{today_label} · Today</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_mid:
        st.markdown(_kpi_html("Resolved", n_resolved, "kpi-purple", "Closed, Cancelled or Rejected"), unsafe_allow_html=True)

    with kpi_right:
        st.markdown(_kpi_html("Backlog", n_backlog, "kpi-acc", "Not yet resolved"), unsafe_allow_html=True)

    # ── Priority breakdown ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    PRIORITY_ROWS = [
        ("High",   "p-high",   "● High"),
        ("Medium", "p-medium", "● Medium"),
        ("Low",    "p-low",    "● Low"),
    ]

    def _pcount(mask_a, priority):
        return int((mask_a & (df["priority"] == priority)).sum())

    mask_new      = (df["created_date"].isin([today_str, yesterday_str])) & (df["issue_type"] == "Bug")
    mask_resolved = df["status"].isin(RESOLVED_STATUSES)
    mask_backlog  = ~mask_resolved

    rows_html = ""
    for priority, css, label in PRIORITY_ROWS:
        rows_html += f"""
            <tr>
                <td><span class="{css}">{label}</span></td>
                <td>{_pcount(mask_new, priority)}</td>
                <td>{_pcount(mask_resolved, priority)}</td>
                <td>{_pcount(mask_backlog, priority)}</td>
            </tr>"""

    _, tbl_col, _ = st.columns([1, 10, 1])
    with tbl_col:
        st.markdown(
            f"""
            <table class="priority-table">
                <thead>
                    <tr>
                        <th>Priority</th>
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

    n_no_date = int(open_df["planned_completion_date"].isna().sum())
    n_overdue = int(df["is_overdue"].sum())
    n_cr      = int(df["defect_type"].str.contains("Change Request", na=False).sum())
    n_retest  = int((df["status"] == "Retest").sum())

    h1, h2, h3, h4 = st.columns(4)
    for col, (label, value, css, subtitle) in zip(
        [h1, h2, h3, h4],
        [
            ("No Completion Date", n_no_date, "kpi-amber",  "Open defects without a date"),
            ("Overdue",            n_overdue, "kpi-red",    "Past planned completion date"),
            ("Change Requests",    n_cr,      "kpi-purple", "Defect type: Change Request"),
            ("In Retest",          n_retest,  "kpi-acc",    "Status: Retest"),
        ],
    ):
        with col:
            st.markdown(_kpi_html(label, value, css, subtitle), unsafe_allow_html=True)

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
    st.markdown('<div class="section-title">Open Defects by Date &amp; Workstream (next 14 days)</div>', unsafe_allow_html=True)

    upcoming = [today + timedelta(days=i) for i in range(14)]
    range_df = ws_df[ws_df["planned_completion_date"].isin(upcoming)]

    if range_df.empty:
        st.info("No open defects with planned completion dates in the next 14 days.")
    else:
        top_ws = (
            range_df.groupby("workstream").size()
            .sort_values(ascending=False)
            .head(5)
            .index.tolist()
        )

        pivot = (
            range_df[range_df["workstream"].isin(top_ws)]
            .groupby(["planned_completion_date", "workstream"])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=top_ws, fill_value=0)
        )
        pivot = pivot[pivot.sum(axis=1) > 0]

        header_cells = "".join(f"<th>{ws}</th>" for ws in top_ws)
        rows_html = ""
        for d, row in pivot.iterrows():
            cells = "".join(f"<td>{int(row[ws])}</td>" for ws in top_ws)
            rows_html += f"<tr><td style='text-align:left'>{_ordinal(d)}</td>{cells}</tr>"

        st.markdown(f"""
        <table class="priority-table">
            <thead><tr><th style='text-align:left'>Date</th>{header_cells}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

