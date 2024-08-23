
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
# Single click run
""")

uploaded_files = st.file_uploader(
    "Choose one or more CSV files", accept_multiple_files=True
)
for uploaded_file in uploaded_files:
    bytes_data = uploaded_file.read()
    # st.write("Filename:", uploaded_file.name)
    # st.write(bytes_data)

left, middle, right = st.columns(3, vertical_alignment="bottom")
N0 = left.number_input("N0 parameter", min_value=1, value=1000)

if st.button("Process data!"):

    with st.spinner('Processing...'):
        example_process.run(csv=uploaded_file.name, N0=N0)

    tab1, tab2 = st.tabs([":material/Table: Processed data", ":material/show_chart: Plots"])

    # tab1.subheader("Processed data table.")
    tab1.write(st.session_state["data"])

    df = st.session_state["data"]#
    fig = px.line(df, y='soil_moisture', title='Soil moisture time series')

    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    tab2.plotly_chart(fig, use_container_width=True)