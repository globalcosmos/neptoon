import streamlit as st
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
    c1.number_input(
        label="Avg Lattice Water",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.avg_lattice_water,
        key="input_sensor_avg_lattice_water",
        min_value=0.0,
        max_value=0.5,
        step=0.001,
    )
    # Avg soil organic carbon
    c2.number_input(
        label="Avg Soil Organic Carbon",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.avg_soil_organic_carbon,
        key="input_sensor_avg_soil_organic_carbon",
        min_value=0.0,
        max_value=0.5,
        step=0.001,
    )
    # Avg dry_soil_bulk_density
    c1.number_input(
        label="Avg dry_soil_bulk_density",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.avg_dry_soil_bulk_density,
        key="input_sensor_avg_dry_soil_bulk_density",
        min_value=0.1,
        max_value=3.0,
        step=0.01,
    )
    # mean_pressure
    c2.number_input(
        label="Mean pressure",
        value=st.session_state["yaml"].sensor_config.sensor_info.mean_pressure,
        key="input_sensor_mean_pressure",
        min_value=1.0,
        max_value=1300.0,
        step=0.1,
    )
    # beta_coefficient
    c1.number_input(
        label="Beta coefficient",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.beta_coefficient,
        key="input_sensor_beta_coefficient",
        min_value=0.0,
        max_value=1.0,
        step=0.0001,
    )
    # Site_cutoff_rigidity
    c2.number_input(
        label="Site cutoff rigidity",
        value=st.session_state[
            "yaml"
        ].sensor_config.sensor_info.site_cutoff_rigidity,
        key="input_sensor_site_cutoff_rigidity",
        min_value=0.0,
        max_value=19.0,
        step=0.01,
    )
    # N0
    c1.number_input(
        label="$N_0$",
        value=st.session_state["yaml"].sensor_config.sensor_info.N0,
        key="input_sensor_N0",
        min_value=1,
        max_value=100000,
        step=1,
    )
    ################################
    st.subheader("3. Apply changes")
    ################################

    from datetime import datetime

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
            datetime.combine(
                st.session_state["input_sensor_install_date"],
                datetime.min.time(),
            )
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
