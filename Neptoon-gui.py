import streamlit as st
# Icons: https://fonts.google.com/icons?icon.set=Material+Symbols&icon.style=Rounded

st.set_page_config(
    page_title="Neptoon GUI",
    page_icon="docs/logo2.svg", #"👋",
)

st.logo(
    "docs/logo2.svg",
    link="https://codebase.helmholtz.cloud/cosmos/neptoon_documentation",
    # icon_image=LOGO_URL_SMALL,
)

# Initialize session state
if 'config_name' not in st.session_state:
    st.session_state.config_name = 'Sensor_A42'
if 'config_changed' not in st.session_state:
    st.session_state.config_changed = False

pages = [
    # st.Page(
    #     "GUI/Welcome.py",
    #     title="Welcome"
    # ),
    st.Page(
        "GUI/Configuration.py",
        title=st.session_state.config_name,
        icon=":material/warning:" if st.session_state.config_changed else ":material/check:"
    ),
    st.Page(
        "GUI/Calibration.py",
        title="Calibration",
        icon=":material/adjust:"
    ),
    st.Page(
        "GUI/Single_click_run.py",
        title="Single click run",
        icon=":material/web_traffic:"
    ),
]

pg = st.navigation(pages)
pg.run()

