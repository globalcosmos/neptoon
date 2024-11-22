import streamlit as st
import logging
from streamlit.logger import get_logger
import pandas as pd

# import example_calibration_gui

import plotly.express as px

import example_process.example_calibration


class StreamlitLogHandler(logging.Handler):
    def __init__(self, widget_update_func):
        super().__init__()
        self.widget_update_func = widget_update_func

    def emit(self, record):
        msg = self.format(record)
        self.widget_update_func(msg)


logger = get_logger(example_process.example_calibration.__name__)
handler = StreamlitLogHandler(st.sidebar.empty().code)
logger.addHandler(handler)


def config_changed():
    st.session_state.config_changed = True


st.markdown(
    """
# :material/adjust: Calibration
In order to find the $N_0$ value, a CRNS probe needs to be calibrated on ground truth data, e.g., soil samples or TDR time serieses.
"""
)

df = pd.read_csv("example_process/example_data/Sheepdrove2-calibration.csv")
st.write(df)

# st.markdown(
#     """
# ## Soil sampling data
# Upload your CSV files with soil sampling data here.
# """
# )
# sampling_uploaded_files = st.file_uploader(
#     "Choose one or more CSV files", accept_multiple_files=True, key="eins"
# )

# st.markdown(
#     """
# ## CRNS data
# Upload your CRNS data here.
# """
# )


# crns_uploaded_files = st.file_uploader(
#     "Choose one or more CSV files", accept_multiple_files=True, key="zwei"
# )

# if (len(sampling_uploaded_files) > 0) and (len(crns_uploaded_files) > 0):

# left, middle, right = st.columns(3, vertical_alignment="bottom")
# N0 = left.number_input(
#     "N0 parameter", min_value=1, value=1000, on_change=config_changed
# )

if st.button("Weight and optimize!"):

    with st.spinner("Processing..."):

        from example_process.example_calibration import calibrate

        N0, crns_data, data = calibrate(
            # sampling_csv=sampling_uploaded_files[0].name,
            # crns_csv=crns_uploaded_files[0].name,
            sampling_csv="example_process/example_data/Sheepdrove2-calibration.csv",
            crns_csv="example_process/example_data/Sheepdrove2-CRNS.csv",
        )

        # st.write(st.session_state["text_N0_calibrated"])
        st.write("Estimated N0 = %.0f" % N0)

        tab1, tab2 = st.tabs(
            [
                # ":material/Table: Sampling data",
                ":material/Table: Processed data",
                ":material/show_chart: Plots",
            ]
        )

        # tab1.subheader("Processed data table.")
        # tab1.write(st.session_state["data_calib"])
        # tab2.write(st.session_state["data_calib_processed"])
        tab1.write(data)

        df = st.session_state.config_obj.data_hub.crns_data_frame

        # fig = px.line(df, y="soil_moisture", title="Soil moisture time series")
        fig = px.line(
            crns_data,
            y="SoilMoisture_volumetric_MovAvg24h",
            title="Soil moisture time series",
        )

        fig.add_scatter(
            x=data["calibration_day"],
            y=data["field_average_soil_moisture_volumetric"],
            mode="markers",
            marker=dict(size=10, color="red"),
        )

        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list(
                    [
                        dict(
                            count=1,
                            label="1m",
                            step="month",
                            stepmode="backward",
                        ),
                        dict(
                            count=6,
                            label="6m",
                            step="month",
                            stepmode="backward",
                        ),
                        dict(
                            count=1,
                            label="YTD",
                            step="year",
                            stepmode="todate",
                        ),
                        dict(
                            count=1,
                            label="1y",
                            step="year",
                            stepmode="backward",
                        ),
                        dict(step="all"),
                    ]
                )
            ),
        )

        tab2.plotly_chart(fig, use_container_width=True)

        # df = st.session_state["data_to_plot_ts"]
        # ds = st.session_state["data_to_plot_sc"]
        # # fig = px.line(df, y="soil_moisture", title="Soil moisture time series")
        # # fig = px.scatter(ds, y="soil_moisture", title="Soil moisture time series")

        # import plotly.graph_objects as go

        # fig = go.Figure()

        # # Add traces
        # fig.add_trace(
        #     go.Scatter(x=ds.index, y=ds.values, mode="markers", name="markers")
        # )
        # fig.add_trace(
        #     go.Scatter(x=df.index, y=df.values, mode="lines", name="lines")
        # )

        # fig.update_xaxes(
        #     rangeslider_visible=True,
        #     rangeselector=dict(
        #         buttons=list(
        #             [
        #                 dict(
        #                     count=1,
        #                     label="1m",
        #                     step="month",
        #                     stepmode="backward",
        #                 ),
        #                 dict(
        #                     count=6,
        #                     label="6m",
        #                     step="month",
        #                     stepmode="backward",
        #                 ),
        #                 dict(
        #                     count=1,
        #                     label="YTD",
        #                     step="year",
        #                     stepmode="todate",
        #                 ),
        #                 dict(
        #                     count=1,
        #                     label="1y",
        #                     step="year",
        #                     stepmode="backward",
        #                 ),
        #                 dict(step="all"),
        #             ]
        #         )
        #     ),
        # )

        # tab3.plotly_chart(fig, use_container_width=True)


# left, middle, right = st.columns(3, vertical_alignment="bottom")
# bd = left.slider(
#     "Bulk density",
#     min_value=0.01,
#     max_value=2.65,
#     value=1.6,
#     on_change=config_changed,
# )

# if st.button("Calibrate!"):
#     st.write("Nothing to do yet.")
