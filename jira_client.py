import os
from datetime import date, datetime

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

load_dotenv()


def _cfg(key: str) -> str:
    """Read from Streamlit secrets first, fall back to environment variables."""
    try:
        return st.secrets[key]
    except (KeyError, AttributeError, Exception):
        return os.getenv(key)


JIRA_BASE_URL = _cfg("JIRA_BASE_URL")
JIRA_EMAIL    = _cfg("JIRA_EMAIL")
JIRA_API_TOKEN = _cfg("JIRA_API_TOKEN")
PROJECT_KEY   = _cfg("JIRA_PROJECT_KEY")
FILTER_ID     = _cfg("JIRA_FILTER_ID")

# ── Custom field mappings ─────────────────────────────────────────────────────
# Replace the placeholder IDs with the real ones from your Jira instance.
# To find them: Jira → Project Settings → Fields, or call:
#   GET /rest/api/3/field  and search for the field name in the response.
CUSTOM_FIELD_MAP = {
    "customfield_10173": "workstream",               # Workstream
    "customfield_10112": "defect_type",              # Defect Type
    "customfield_10064": "planned_completion_date",  # Planned Completion Date
    "customfield_10117": "business_process_l1",      # Business Process Hierarchy L1
    "customfield_10110": "responsible_org",          # Responsible Organization
    "customfield_10700": "pre_test",                 # Pre-test
    "customfield_10105": "stage_found",              # Stage Found
}

INACTIVE_STATUSES = {"Closed", "Rejected", "Cancelled", "Deferred"}

SEARCH_ENDPOINT = "/rest/api/3/search/jql"
PAGE_SIZE = 100


def _auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)


def _extract_field(fields: dict, jira_key: str) -> str:
    """Safely pull a field value; returns 'Unassigned' when absent or null."""
    value = fields.get(jira_key)
    if value is None:
        return "Unassigned"
    # Multi-select / array fields (e.g. Workstream, Defect Type)
    if isinstance(value, list):
        labels = [
            item.get("value") or item.get("name") or item.get("displayName", "")
            for item in value
            if isinstance(item, dict)
        ]
        return ", ".join(filter(None, labels)) or "Unassigned"
    # Single-select option fields use "value" key; user/status objects use "name"/"displayName"
    if isinstance(value, dict):
        return (
            value.get("value")
            or value.get("displayName")
            or value.get("name")
            or "Unassigned"
        )
    return str(value)


def _fetch_page(jql: str, next_page_token: str | None, session: requests.Session) -> dict:
    params = {
        "jql": jql,
        "maxResults": PAGE_SIZE,
        "fields": ",".join([
            "summary",
            "assignee",
            "priority",
            "status",
            "created",
            "issuetype",
            *CUSTOM_FIELD_MAP.keys(),
        ]),
    }
    if next_page_token:
        params["nextPageToken"] = next_page_token

    resp = session.get(
        f"{JIRA_BASE_URL}{SEARCH_ENDPOINT}",
        params=params,
        auth=_auth(),
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(
            f"Jira API error {resp.status_code}: {resp.text[:400]}"
        )
    return resp.json()


def get_issues() -> pd.DataFrame:
    """Fetch all issues for the project and return a clean DataFrame."""
    if not all([JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
        raise EnvironmentError(
            "Missing one or more required environment variables: "
            "JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN"
        )
    if not FILTER_ID and not PROJECT_KEY:
        raise EnvironmentError(
            "Set either JIRA_FILTER_ID (recommended) or JIRA_PROJECT_KEY in your .env file."
        )

    if FILTER_ID:
        jql = f"filter = {FILTER_ID} ORDER BY created DESC"
    else:
        jql = f"project = {PROJECT_KEY} ORDER BY created DESC"
    session = requests.Session()
    rows = []
    next_page_token = None

    while True:
        data = _fetch_page(jql, next_page_token, session)
        issues = data.get("issues", [])

        for issue in issues:
            f = issue.get("fields", {})
            row = {
                "issue_key": issue.get("key", ""),
                "summary": f.get("summary", ""),
                "assignee": _extract_field(f, "assignee"),
                "priority": _extract_field(f, "priority"),
                "status": _extract_field(f, "status"),
                "issue_type": _extract_field(f, "issuetype"),
                "created_date": (f.get("created") or "")[:10],
            }
            for jira_key, col_name in CUSTOM_FIELD_MAP.items():
                row[col_name] = _extract_field(f, jira_key)

            rows.append(row)

        next_page_token = data.get("nextPageToken")
        if not issues or not next_page_token:
            break

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # ── Derived columns ───────────────────────────────────────────────────────
    df["is_active"] = ~df["status"].isin(INACTIVE_STATUSES)

    df["planned_completion_date"] = pd.to_datetime(
        df["planned_completion_date"], errors="coerce"
    ).dt.date

    today = date.today()
    df["is_overdue"] = (
        df["is_active"]
        & df["planned_completion_date"].notna()
        & (df["planned_completion_date"] < today)
    )

    return df
