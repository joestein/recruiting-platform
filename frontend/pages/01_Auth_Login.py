import streamlit as st

from utils.api_client import APIClient


def init_session():
    if "api_client" not in st.session_state:
        st.session_state["api_client"] = APIClient()
    if "access_token" not in st.session_state:
        st.session_state["access_token"] = None
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None


def main():
    st.set_page_config(page_title="Login / Register", layout="centered")
    init_session()
    api: APIClient = st.session_state["api_client"]

    st.title("Login / Register")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        password = password.strip()
        if st.button("Login"):
            token = api.login(email=email, password=password)
            if token:
                st.session_state["access_token"] = token
                st.session_state["api_client"] = APIClient(access_token=token)
                user = st.session_state["api_client"].me()
                st.session_state["current_user"] = user
                st.success(f"Logged in as {user['email']}")
            else:
                st.error("Invalid credentials")

    with tab_register:
        st.subheader("Register")
        email_r = st.text_input("Email", key="reg_email")
        password_r = st.text_input("Password", type="password", key="reg_password")
        password_r = password_r.strip()
        org_name_r = st.text_input("Organization Name", key="reg_org_name")

        if st.button("Register"):
            ok = api.register(email=email_r, password=password_r, org_name=org_name_r)
            if ok:
                st.success("Registration successful. You can now log in.")
            else:
                st.error("Registration failed")


if __name__ == "__main__":
    main()
