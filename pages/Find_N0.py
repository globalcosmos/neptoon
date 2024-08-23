import streamlit as st
import example_process
import logging
from streamlit.logger import get_logger
import plotly.figure_factory as ff
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

class StreamlitLogHandler(logging.Handler):
    def __init__(self, widget_update_func):
        super().__init__()
        self.widget_update_func = widget_update_func

    def emit(self, record):
        msg = self.format(record)
        self.widget_update_func(msg)

logger = get_logger(example_process.__name__)
handler = StreamlitLogHandler(st.sidebar.empty().code)
logger.addHandler(handler)

st.markdown("""
# Find $N_0$
""")

uploaded_files = st.file_uploader(
    "Choose one or more CSV files", accept_multiple_files=True
)
for uploaded_file in uploaded_files:
    bytes_data = uploaded_file.read()
    # st.write("Filename:", uploaded_file.name)
    # st.write(bytes_data)

left, middle, right = st.columns(3, vertical_alignment="bottom")
bd = left.slider("Bulk density", min_value=0.01, max_value=2.65, value=1.6)

if st.button("Find N0!"):
    st.write("OK.")