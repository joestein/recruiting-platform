import streamlit as st

st.set_page_config(page_title="Recruiting Platform", layout="wide")

st.sidebar.title("Recruiting Platform")
st.sidebar.write("Use the pages on the left to navigate.")

st.title("Welcome to your Recruiting Platform")

st.write(
    """
This is the main entry point for your SaaS recruiting application.

Use the sidebar to:
- Log in / register
- Chat with the recruiter assistant
- View jobs & candidates
- Upload resumes and job descriptions
"""
)
