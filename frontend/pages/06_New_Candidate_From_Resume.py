import streamlit as st

from utils.api_client import APIClient


def init_session():
    if "api_client" not in st.session_state:
        st.session_state["api_client"] = APIClient()
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None
    if "candidate_chat" not in st.session_state:
        st.session_state["candidate_chat"] = []


def main():
    st.set_page_config(page_title="New Candidate from Resume", layout="wide")
    init_session()

    api: APIClient = st.session_state["api_client"]
    token = st.session_state["access_token"]

    st.title("Create Candidate from Resume")

    if not token:
        st.warning("You must be logged in to use this page. Go to the **Login / Register** page.")
        return

    left, right = st.columns([2, 2])

    with left:
        st.subheader("Upload Resume")

        uploaded_file = st.file_uploader("Resume file (PDF, DOCX, TXT)", type=None)
        extra_notes = st.text_area(
            "Recruiter notes (optional)",
            placeholder="Any extra context about this candidate...",
        )

        if st.button("Create Candidate from Resume", type="primary") and uploaded_file is not None:
            with st.spinner("Creating candidate from resume..."):
                result = api.create_candidate_from_resume(uploaded_file, notes=extra_notes)

            if not result:
                st.error("Failed to create candidate from resume.")
            else:
                cand = result["candidate"]
                summary = result["summary"]

                st.success(f"Created candidate #{cand['id']}: {cand['full_name']}")

                st.write("**Backend summary:**")
                st.write(summary)

                st.session_state["candidate_chat"] = []
                st.session_state["candidate_chat"].append(
                    {"role": "assistant", "content": summary}
                )
                st.session_state["candidate_chat"].append(
                    {
                        "role": "assistant",
                        "content": f"You can now ask in the Recruiter Chat: "
                                   f"`summarize candidate {cand['id']}` "
                                   "or match jobs for this candidate.",
                    }
                )
                st.session_state["last_created_candidate_id"] = cand["id"]

    with right:
        st.subheader("Candidate Assistant (read-only)")

        for msg in st.session_state["candidate_chat"]:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])

        st.info(
            "For interactive Q&A about this candidate, go to the **Recruiter Chat** page and say "
            "`summarize candidate X` using the candidate id created here."
        )


if __name__ == "__main__":
    main()
