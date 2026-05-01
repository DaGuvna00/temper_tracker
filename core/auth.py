import streamlit as st

try:
    from supabase import create_client
except ImportError:
    create_client = None


def get_secret(name, default=None):
    """Safely read Streamlit secrets locally or in Streamlit Cloud."""
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_ANON_KEY = get_secret("SUPABASE_ANON_KEY")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_ANON_KEY and create_client is not None)


def get_supabase_client():
    """Create a Supabase client for the current Streamlit session.

    Do not cache this client globally. Each user needs their own auth session
    so Row Level Security can correctly isolate their data.
    """
    if not USE_SUPABASE:
        return None

    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    access_token = st.session_state.get("sb_access_token")
    refresh_token = st.session_state.get("sb_refresh_token")
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            st.session_state.pop("sb_access_token", None)
            st.session_state.pop("sb_refresh_token", None)
            st.session_state.pop("sb_user", None)

    return client


def current_user_id():
    user = st.session_state.get("sb_user")
    if not user:
        return None
    return user.get("id") if isinstance(user, dict) else getattr(user, "id", None)


def store_auth_session(auth_response):
    session = getattr(auth_response, "session", None)
    user = getattr(auth_response, "user", None)

    if session:
        st.session_state.sb_access_token = session.access_token
        st.session_state.sb_refresh_token = session.refresh_token

    if user:
        st.session_state.sb_user = {
            "id": user.id,
            "email": user.email,
        }


def logout():
    if USE_SUPABASE and current_user_id():
        try:
            get_supabase_client().auth.sign_out()
        except Exception:
            pass
    st.session_state.pop("sb_access_token", None)
    st.session_state.pop("sb_refresh_token", None)
    st.session_state.pop("sb_user", None)


def require_login():
    """Require Supabase email/password login when Supabase is enabled."""
    if not USE_SUPABASE:
        return

    if current_user_id():
        return

    st.title("Temper Tracker")
    st.caption("Sign in so your logs follow you across phone and computer.")

    login_tab, signup_tab = st.tabs(["Log in", "Create account"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            try:
                response = get_supabase_client().auth.sign_in_with_password({
                    "email": email.strip(),
                    "password": password,
                })
                store_auth_session(response)
                st.success("Logged in.")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    with signup_tab:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Create account", use_container_width=True)

        if submitted:
            if new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Use at least 6 characters.")
            else:
                try:
                    response = get_supabase_client().auth.sign_up({
                        "email": new_email.strip(),
                        "password": new_password,
                    })
                    store_auth_session(response)
                    if current_user_id():
                        st.success("Account created. You are logged in.")
                        st.rerun()
                    else:
                        st.success("Account created. Check your email to confirm, then log in.")
                except Exception as e:
                    st.error(f"Signup failed: {e}")

    st.stop()
