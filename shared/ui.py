import streamlit as st
import streamlit.components.v1 as components

def sidebar_api_key():
    """
    Renders the API key input in the sidebar and manages its state.
    Syncs with browser localStorage for persistence across refreshes.
    """
    STORAGE_KEY = "scholar_survey_gemini_api_key"
    
    # Initialize session state
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    # 1. Load from localStorage via JS if session state is empty
    # We use query_params as a bridge to get data from JS to Python
    if not st.session_state.api_key and "api_key_sync" in st.query_params:
        st.session_state.api_key = st.query_params["api_key_sync"]
    
    if not st.session_state.api_key:
        components.html(
            f"""
            <script>
                const key = window.parent.localStorage.getItem('{STORAGE_KEY}');
                if (key) {{
                    const url = new URL(window.parent.location);
                    if (url.searchParams.get('api_key_sync') !== key) {{
                        url.searchParams.set('api_key_sync', key);
                        window.parent.location.href = url.href;
                    }}
                }}
            </script>
            """,
            height=0
        )

    st.sidebar.title("🔑 AI Configuration")
    
    # 2. Save to localStorage when changed
    def on_key_change():
        new_val = st.session_state.api_key_widget
        st.session_state.api_key = new_val
        # The JS execution here is a bit tricky on change, but we can use a dedicated component
        # Streamlit doesn't run the script after on_change immediately in a way that allows easy JS injection
        # but we can set a flag to run it in the main flow.
        st.session_state.api_key_needs_save = True

    api_key_val = st.sidebar.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help="Saved securely in your browser's local storage.",
        key="api_key_widget",
        on_change=on_key_change
    )
    
    if st.session_state.get("api_key_needs_save"):
        components.html(
            f"""
            <script>
                window.parent.localStorage.setItem('{STORAGE_KEY}', '{st.session_state.api_key}');
            </script>
            """,
            height=0
        )
        st.session_state.api_key_needs_save = False

    if not st.session_state.api_key:
        st.sidebar.warning("⚠️ API key missing.")
    else:
        st.sidebar.success("✅ API key active")
        if st.sidebar.button("Clear Saved Key"):
            st.session_state.api_key = ""
            components.html(
                f"""
                <script>
                    window.parent.localStorage.removeItem('{STORAGE_KEY}');
                    const url = new URL(window.parent.location);
                    url.searchParams.delete('api_key_sync');
                    window.parent.location.href = url.href;
                </script>
                """,
                height=0
            )
            st.rerun()
            
    st.sidebar.divider()
    
    return st.session_state.api_key
