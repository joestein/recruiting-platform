import os

import pandas as pd
import requests
import streamlit as st

from utils.api_client import APIClient

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")


def init_session():
    if "api_client" not in st.session_state:
        st.session_state["api_client"] = APIClient()
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None


def fetch_candidates(api_client: APIClient):
    resp = requests.get(f"{API_URL}/candidates", headers=api_client._headers())
    if resp.status_code == 200:
        return resp.json().get("items", [])
    return []


def main():
    st.set_page_config(page_title="Jobs & Candidates", layout="wide")
    init_session()

    api: APIClient = st.session_state["api_client"]
    token = st.session_state["access_token"]

    st.title("Jobs & Candidate Matches")

    if not token:
        st.warning("You must be logged in to view this page. Go to the **Login / Register** page.")
        return

    # Job -> Candidates
    st.header("Job → Candidates")

    col1, col2 = st.columns([2, 1])
    with col1:
        status_filter = st.selectbox(
            "Filter jobs by status",
            options=["", "open", "on_hold", "closed"],
            index=1,
            help="Filter jobs by status (optional).",
        )
    with col2:
        search_q = st.text_input(
            "Search jobs by title (optional)",
            value="",
            help="Type part of a job title to filter (optional).",
        )

    jobs = api.get_jobs(status_filter=status_filter or None, q=search_q or None)
    if not jobs:
        st.info("No jobs found for your organization with the current filters.")
    else:
        job_options = {f"[#{j['id']}] {j['title']} ({j.get('location') or 'N/A'})": j for j in jobs}
        job_label_list = list(job_options.keys())
        selected_label = st.selectbox("Select job", options=job_label_list)
        selected_job = job_options[selected_label]
        selected_job_id = selected_job["id"]

        st.markdown(
            f"**Selected job:** #{selected_job_id} — {selected_job['title']} "
            f"({selected_job.get('location') or 'location N/A'})"
        )

        if st.button("Find candidate matches for this job"):
            matches = api.match_candidates_for_job(job_id=selected_job_id, limit=50)
            if not matches:
                st.warning("No matching candidates found for this job yet.")
            else:
                df = pd.DataFrame(matches)
                cols = [
                    "score",
                    "strategy",
                    "candidate_id",
                    "full_name",
                    "current_title",
                    "current_company",
                    "location",
                    "reason",
                ]
                df = df[[c for c in cols if c in df.columns]]
                st.subheader("Candidate matches")
                st.dataframe(df, use_container_width=True)
                st.caption(
                    "Scores are 0–100. 'strategy' shows whether naive keyword or OpenAI embeddings were used. "
                    "'reason' explains why a candidate was considered a good match."
                )

    st.markdown("---")
    st.header("Candidate → Jobs")

    candidates = fetch_candidates(api)
    if not candidates:
        st.info("No candidates found for your organization yet.")
        return

    cand_options = {f"[#{c['id']}] {c['full_name']}": c for c in candidates}
    cand_label_list = list(cand_options.keys())
    selected_cand_label = st.selectbox("Select candidate", options=cand_label_list)
    selected_cand = cand_options[selected_cand_label]
    selected_cand_id = selected_cand["id"]

    st.markdown(
        f"**Selected candidate:** #{selected_cand_id} — {selected_cand['full_name']} "
        f"({selected_cand.get('current_title') or 'title N/A'} @ "
        f"{selected_cand.get('current_company') or 'company N/A'})"
    )

    if st.button("Find job matches for this candidate"):
        matches_jobs = api.match_jobs_for_candidate(candidate_id=selected_cand_id, limit=50)
        if not matches_jobs:
            st.warning("No job matches found for this candidate yet.")
        else:
            df_jobs = pd.DataFrame(matches_jobs)
            cols_jobs = [
                "score",
                "strategy",
                "job_id",
                "title",
                "location",
                "status",
                "reason",
            ]
            df_jobs = df_jobs[[c for c in cols_jobs if c in df_jobs.columns]]

            st.subheader("Job matches")
            st.dataframe(df_jobs, use_container_width=True)
            st.caption(
                "Scores are 0–100. 'strategy' shows whether naive keyword or OpenAI embeddings were used. "
                "'reason' explains why a job was considered a good match."
            )


if __name__ == "__main__":
    main()
