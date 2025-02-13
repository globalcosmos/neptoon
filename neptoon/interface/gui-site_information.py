import streamlit as st
import logging
from streamlit.logger import get_logger
import io
from pathlib import Path
from neptoon_gui_utils import *
import pandas as pd

st.title(":material/info: Site information")

if not st.session_state["yaml_checked"]:
    st.warning("You need to select a configuration first.")
else:

    #######################
    st.subheader("1. Site")
    #######################

    c1, c2 = st.columns(2)

    # Name
    c1.text_input(
        label="Name",
        value=st.session_state["yaml"].sensor_config.sensor_info.name,
        key="input_sensor_name",
    )

    # Country
    c2.text_input(
        label="Country",
        value=st.session_state["yaml"].sensor_config.sensor_info.country,
        key="input_sensor_country",
    )

    # Identifier
    c1.text_input(
        label="Identifier",
        value=st.session_state["yaml"].sensor_config.sensor_info.identifier,
        key="input_sensor_identifier",
    )

    c1, c2 = st.columns(2)

    # Install date
    c1.date_input(
        label="Install date",
        value=st.session_state["yaml"].sensor_config.sensor_info.install_date,
        key="input_sensor_install_date",
    )

    # Timezone
    c2.number_input(
        label="Timezone",
        value=int(
            st.session_state["yaml"].sensor_config.sensor_info.time_zone
        ),
        key="input_sensor_time_zone",
        min_value=-12,
        max_value=14,
    )

    @st.fragment
    def make_location():
        c1, c2 = st.columns(2)

        # Latitude
        c1.number_input(
            label="Latitude",
            value=float(
                st.session_state["yaml"].sensor_config.sensor_info.latitude
            ),
            key="input_sensor_latitude",
            min_value=-180.0,
            max_value=180.0,
            format="%0.5f",
        )

        # Longitude
        c1.number_input(
            label="Longitude",
            value=float(
                st.session_state["yaml"].sensor_config.sensor_info.longitude
            ),
            key="input_sensor_longitude",
            min_value=-90.0,
            max_value=90.0,
            format="%0.5f",
        )

        # Elevation
        c1.number_input(
            label="Elevation",
            value=float(
                st.session_state["yaml"].sensor_config.sensor_info.elevation
            ),
            key="input_sensor_elevation",
            min_value=-1000.0,
            max_value=10000.0,
            format="%0.1f",
            step=1.0,
        )

        map_data = pd.DataFrame(
            dict(
                lat=[
                    st.session_state["input_sensor_latitude"],
                    st.session_state["input_sensor_latitude"],
                    st.session_state["input_sensor_latitude"],
                    # st.session_state["yaml"].sensor_config.sensor_info.latitude,
                ],
                lon=[
                    st.session_state["input_sensor_longitude"],
                    st.session_state["input_sensor_longitude"],
                    st.session_state["input_sensor_longitude"],
                    # st.session_state["yaml"].sensor_config.sensor_info.longitude,
                ],
                size=[5, 100, 200],
            )
        )
        c2.map(map_data, size="size", height=300)
        c2.write("Circle radius: 5, 100, 200 m")

    make_location()

    ######################################
    st.subheader("2. Physical parameters")
    ######################################

    c1, c2 = st.columns(2)

    # Avg Lattice Water
    c1.text_input(
        label="Avg Lattice Water",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.avg_lattice_water,
        key="input_sensor_avg_lattice_water",
    )
    # Avg soil organic carbon
    c2.text_input(
        label="Avg Lattice Water",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.avg_soil_organic_carbon,
        key="input_sensor_avg_soil_organic_carbon",
    )
    # Avg dry_soil_bulk_density
    c1.text_input(
        label="Avg dry_soil_bulk_density",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.avg_dry_soil_bulk_density,
        key="input_sensor_avg_dry_soil_bulk_density",
    )
    # mean_pressure
    c2.text_input(
        label="Mean pressure",
        value=st.session_state["yaml"].sensor_config.sensor_info.mean_pressure,
        key="input_sensor_mean_pressure",
    )
    # beta_coefficient
    c1.text_input(
        label="Beta coefficient",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.beta_coefficient,
        key="input_sensor_beta_coefficient",
    )
    # Site_cutoff_rigidity
    c2.text_input(
        label="Site cutoff rigidity",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.site_cutoff_rigidity,
        key="input_sensor_site_cutoff_rigidity",
    )
    # N0
    c1.text_input(
        label="$N_0$",
        value=st.session_state["yaml"].sensor_config.sensor_info.N0,
        key="input_sensor_N0",
    )
    ################################
    st.subheader("3. Apply changes")
    ################################

    if st.button("Apply"):
        st.session_state["yaml"].sensor_config.sensor_info.name = (
            st.session_state["input_sensor_name"]
        )
        st.session_state["yaml"].sensor_config.sensor_info.country = (
            st.session_state["input_sensor_country"]
        )
        st.session_state["yaml"].sensor_config.sensor_info.identifier = (
            st.session_state["input_sensor_identifier"]
        )
        st.session_state["yaml"].sensor_config.sensor_info.install_date = (
            st.session_state["input_sensor_install_date"]
        )
        st.session_state["yaml"].sensor_config.sensor_info.time_zone = (
            st.session_state["input_sensor_time_zone"]
        )
        st.session_state["yaml"].sensor_config.sensor_info.latitude = (
            st.session_state["input_sensor_latitude"]
        )
        st.session_state["yaml"].sensor_config.sensor_info.longitude = (
            st.session_state["input_sensor_longitude"]
        )
        st.session_state["yaml"].sensor_config.sensor_info.elevation = (
            st.session_state["input_sensor_elevation"]
        )
        st.session_state[
            "yaml"
        ].sensor_config.sensor_info.site_cutoff_rigidity = st.session_state[
            "input_sensor_site_cutoff_rigidity"
        ]
        st.session_state[
            "yaml"
        ].sensor_config.sensor_info.avg_lattice_water = st.session_state[
            "input_sensor_avg_lattice_water"
        ]
        st.session_state[
            "yaml"
        ].sensor_config.sensor_info.avg_soil_organic_carbon = st.session_state[
            "input_sensor_avg_soil_organic_carbon"
        ]
        st.session_state[
            "yaml"
        ].sensor_config.sensor_info.avg_dry_soil_bulk_density = st.session_state[
            "input_sensor_avg_dry_soil_bulk_density"
        ]
        st.session_state["yaml"].sensor_config.sensor_info.beta_coefficient = (
            st.session_state["input_sensor_beta_coefficient"]
        )
        st.session_state["yaml"].sensor_config.sensor_info.mean_pressure = (
            st.session_state["input_sensor_mean_pressure"]
        )
        st.session_state["yaml"].sensor_config.sensor_info.N0 = (
            st.session_state["input_sensor_N0"]
        )

        st.success("Changes applied :smile:")
