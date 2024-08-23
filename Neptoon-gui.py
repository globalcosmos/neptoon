import logging
import streamlit as st
from streamlit.logger import get_logger

st.set_page_config(
    page_title="Neptoon GUI",
    page_icon="👋",
)

st.logo(
    "docs/logo2.svg",
    link="https://codebase.helmholtz.cloud/cosmos/neptoon_documentation",
    # icon_image=LOGO_URL_SMALL,
)

# class StreamlitLogHandler(logging.Handler):
#     def __init__(self, widget_update_func):
#         super().__init__()
#         self.widget_update_func = widget_update_func

#     def emit(self, record):
#         msg = self.format(record)
#         self.widget_update_func(msg)

# logger = get_logger(example_process.__name__)
# handler = StreamlitLogHandler(st.sidebar.empty().code)
# logger.addHandler(handler)


pages = [
    # "Welcome": [
    st.Page("pages/Welcome.py", title="Welcome"),
    st.Page("pages/Find_N0.py", title="Find N0"),
    st.Page("pages/Single_click_run.py", title="Single click run"),
    ]

pg = st.navigation(pages)
pg.run()


# st.markdown("""
# First GUI test for Neptoon using Streamlit.1
# """)

# uploaded_files = st.file_uploader(
#     "Choose one or more CSV files", accept_multiple_files=True
# )
# for uploaded_file in uploaded_files:
#     bytes_data = uploaded_file.read()
#     st.write("Filename:", uploaded_file.name)
#     # st.write(bytes_data)

# if st.button("Load CSV!"):
#     example_process.run(csv=uploaded_file.name)
#     st.dataframe(st.session_state["data"])

# if st.button("Plot neutrons"):
#     st.line_chart(st.session_state["data"]["soil_moisture"])