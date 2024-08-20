import logging
import example_process
import streamlit as st
from streamlit.logger import get_logger

st.set_page_config(
    page_title="Neptoon GUI",
    page_icon="👋",
)

class StreamlitLogHandler(logging.Handler):
    def __init__(self, widget_update_func):
        super().__init__()
        self.widget_update_func = widget_update_func

    def emit(self, record):
        msg = self.format(record)
        self.widget_update_func(msg)

logger = get_logger(example_process.__name__)
handler = StreamlitLogHandler(st.empty().code)
logger.addHandler(handler)

st.markdown("""
First GUI test for Neptoon using Streamlit.
""")

if st.button("Load CSV!"):
    example_process.run()
    st.dataframe(st.session_state["data"])

if st.button("Plot neutrons"):
    st.line_chart(st.session_state["data"]["soil_moisture"])