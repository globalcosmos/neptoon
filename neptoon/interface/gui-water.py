import streamlit as st

# from pathlib import Path
# from neptoon_gui_utils import cleanup, save_uploaded_file, read_file

# import plotly.graph_objects as go

st.title(":material/water_drop: Water")

if not st.session_state["data_corrections_made"]:
    st.warning("You need to process all neutron corrections first.")
else:

    st.write(
        "Conversion to soil moisture. Future versions will reveal more settings here."
    )

    @st.cache_data(show_spinner="Converting to soil moisture")
    def make_soil_moisture():
        import numpy as np

        st.session_state["yaml"].data_hub.create_neutron_uncertainty_bounds()
        st.session_state["yaml"].data_hub.produce_soil_moisture_estimates()
        dfx = st.session_state["yaml"].data_hub.crns_data_frame
        st.session_state["yaml"].data_hub.crns_data_frame.loc[
            dfx["soil_moisture"] < 0, "soil_moisture"
        ] = np.nan
        st.session_state["yaml"].data_hub.crns_data_frame.loc[
            dfx["soil_moisture"] > 1, "soil_moisture"
        ] = np.nan
        st.session_state["yaml"].data_hub.crns_data_frame.loc[
            dfx["soil_moisture_uncertainty_lower"] < 0,
            "soil_moisture_uncertainty_lower",
        ] = np.nan
        st.session_state["yaml"].data_hub.crns_data_frame.loc[
            dfx["soil_moisture_uncertainty_lower"] > 1,
            "soil_moisture_uncertainty_lower",
        ] = np.nan
        st.session_state["yaml"].data_hub.crns_data_frame.loc[
            dfx["soil_moisture_uncertainty_upper"] < 0,
            "soil_moisture_uncertainty_upper",
        ] = np.nan
        st.session_state["yaml"].data_hub.crns_data_frame.loc[
            dfx["soil_moisture_uncertainty_upper"] > 1,
            "soil_moisture_uncertainty_upper",
        ] = np.nan
        st.session_state["yaml"].data_hub.crns_data_frame.loc[
            dfx["crns_measurement_depth"] < 0, "crns_measurement_depth"
        ] = np.nan
        st.session_state["yaml"].data_hub.crns_data_frame.loc[
            dfx["crns_measurement_depth"] > 100, "crns_measurement_depth"
        ] = np.nan

    if st.button("Convert!", type="primary"):
        make_soil_moisture()
        st.session_state["data_converted"] = True

if st.session_state["data_converted"]:

    @st.fragment
    def make_water_plot():
        import plotly.express as px

        tab1, tab2 = st.tabs(
            [
                ":material/Table: Processed data table",
                ":material/show_chart: Plots",
            ]
        )

        columns_to_show = [
            "soil_moisture",
            "soil_moisture_uncertainty_lower",
            "soil_moisture_uncertainty_upper",
            "crns_measurement_depth",
        ]

        tab1.dataframe(
            st.session_state["yaml"].data_hub.crns_data_frame[columns_to_show]
        )

        selected_columns = tab2.multiselect(
            "Which columns would you like to view?",
            options=columns_to_show,
            default="soil_moisture",
        )

        # filtered_data = st.session_state["yaml"].data_hub.crns_data_frame[
        #     selected_columns
        # ]

        tab2.plotly_chart(
            px.line(
                st.session_state["yaml"].data_hub.crns_data_frame[
                    columns_to_show
                ],
                y=selected_columns,
            ),
            use_container_width=True,
        )

    make_water_plot()
