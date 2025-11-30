import streamlit as st

from utils.api_client import APIClient


def init_session():
    if "api_client" not in st.session_state:
        st.session_state["api_client"] = APIClient()
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []  # {"role": "user"/"agent", "content": str}


def main():
    st.set_page_config(page_title="Recruiter Chat", layout="wide")
    init_session()

    api: APIClient = st.session_state["api_client"]
    token = st.session_state["access_token"]

    st.title("Recruiter Assistant")

    if not token:
        st.warning("You must be logged in to use the chat. Go to the **Login / Register** page.")
        return

    left, right = st.columns([3, 1])

    with right:
        st.subheader("Quick Commands")

        if st.button("List jobs"):
            st.session_state["chat_messages"].append({"role": "user", "content": "List jobs"})

        if st.button("Show open jobs"):
            st.session_state["chat_messages"].append({"role": "user", "content": "Show open jobs"})

        if st.button("List candidates"):
            st.session_state["chat_messages"].append({"role": "user", "content": "List candidates"})

        if st.button("Show candidates in New York"):
            st.session_state["chat_messages"].append(
                {"role": "user", "content": "Show candidates in New York"}
            )

        st.markdown("---")
        st.write(
            "You can ask things like:\n"
            "- `create a new job for a Senior Backend Engineer in NYC...`\n"
            "- `match candidates for job 3`\n"
            "- `match jobs for candidate 7`\n"
            "- `summarize candidate 5`\n"
        )

        st.markdown("---")
        st.subheader("Create job from job req")

        job_req_file = st.file_uploader("Upload job description", key="job_req_file")
        job_req_notes = st.text_area(
            "Notes (optional)",
            key="job_req_notes",
            height=80,
            placeholder="Any extra comments or constraints about this role...",
        )

        if st.button("Create job from uploaded req"):
            if job_req_file is None:
                st.error("Please upload a job description file first.")
            else:
                with st.spinner("Creating job from job req..."):
                    result = api.create_job_from_req(job_req_file, notes=job_req_notes)

                if not result:
                    st.error("Failed to create job from uploaded job req.")
                else:
                    summary = result["summary"]
                    job = result["job"]
                    st.session_state["chat_messages"].append(
                        {
                            "role": "user",
                            "content": f"I uploaded a job description file '{result['filename']}'.",
                        }
                    )
                    st.session_state["chat_messages"].append(
                        {"role": "agent", "content": summary}
                    )
                    st.success(f"Created job #{job['id']}: {job['title']}")

    with left:
        st.subheader("Chat")

        for msg in st.session_state["chat_messages"]:
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask about jobs, candidates, or pipelines...")

        if user_input:
            st.session_state["chat_messages"].append({"role": "user", "content": user_input})
            reply = api.agent_chat(message=user_input)
            st.session_state["chat_messages"].append({"role": "agent", "content": reply})
            st.experimental_rerun()


if __name__ == "__main__":
    main()
