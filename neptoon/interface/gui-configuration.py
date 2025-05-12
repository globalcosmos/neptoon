import streamlit as st
import atexit
from pathlib import Path
from neptoon_gui_utils import cleanup, save_uploaded_file, read_file
from neptoon.io.read import ConfigurationManager
from neptoon.workflow import ProcessWithConfig

st.title(":material/settings: Configuration")
"""
We keep all the different settings and parameters well organized in configuration files.
They are simple text files in [YAML format](https://en.wikipedia.org/wiki/YAML),
editable by any text editor.
To initialize your data processing, you can either use existing exemplary configuration files, or upload your own.
"""

##################################
st.subheader("1. Site and sensor")
"""
The first file is site-specific, it contains all the relevant information for your individual sensor.
"""
##################################


st.selectbox(
    "Select a configuration:",
    [
        "Custom configuration...",
        "Example: COSMOS Europe",
        # "Example: Hydroinnova",
        # "Example: Styx Neutronica",
        "Example: Finapp",
    ],
    key="config_sensor_selected",
)

if st.session_state["config_sensor_selected"] == "Example: COSMOS Europe":
    st.session_state["config_sensor_file"] = (
        Path(__file__).parent / "default_configuration" / "FSC001_station.yaml"
    )
    st.success(
        ":material/check: Using **{:}** for sensor and site configuration.".format(
            st.session_state["config_sensor_selected"]
        )
    )
    with st.expander("View"):
        st.code(
            read_file(st.session_state["config_sensor_file"]),
            language="yaml",
        )

elif st.session_state["config_sensor_selected"] == "Example: Hydroinnova":
    st.session_state["config_sensor_file"] = (
        Path(__file__).parent / "default_configuration" / "A101_station.yaml"
    )
    st.success(
        ":material/check: Using **{:}** for sensor and site configuration.".format(
            st.session_state["config_sensor_selected"]
        )
    )
    with st.expander("View"):
        st.code(
            read_file(st.session_state["config_sensor_file"]),
            language="yaml",
        )

elif st.session_state["config_sensor_selected"] == "Example: Styx Neutronica":
    st.session_state["config_sensor_file"] = (
        Path(__file__).parent / "default_configuration" / "StyxHC.yaml"
    )
    st.success(
        ":material/check: Using **{:}** for sensor and site configuration.".format(
            st.session_state["config_sensor_selected"]
        )
    )
    with st.expander("View"):
        st.code(
            read_file(st.session_state["config_sensor_file"]),
            language="yaml",
        )

elif st.session_state["config_sensor_selected"] == "Example: Finapp":
    st.session_state["config_sensor_file"] = (
        Path(__file__).parent / "default_configuration" / "FinApp01.yaml"
    )
    st.success(
        ":material/check: Using **{:}** for sensor and site configuration.".format(
            st.session_state["config_sensor_selected"]
        )
    )
    with st.expander("View"):
        st.code(
            read_file(st.session_state["config_sensor_file"]),
            language="yaml",
        )

elif st.session_state["config_sensor_selected"] == "Custom configuration...":
    uploaded_file = st.file_uploader(
        "Upload your configuration file",
        type={"yaml", "yml"},
        key="config_sensor_uploaded",
        label_visibility="collapsed",
    )
    if uploaded_file:
        # File upload
        st.session_state["config_sensor_uploaded_name"] = uploaded_file.name

        temp_file_path = save_uploaded_file(uploaded_file)
        atexit.register(cleanup, temp_file_path)

        st.session_state["config_sensor_uploaded_file"] = temp_file_path
        st.session_state["config_sensor_file"] = temp_file_path

    if st.session_state["config_sensor_uploaded_file"]:
        # Already uploaded
        st.success(
            ":material/check: Using **{:}** for sensor and site configuration.".format(
                st.session_state["config_sensor_uploaded_name"]
            )
        )
        with st.expander("View"):
            st.code(
                read_file(st.session_state["config_sensor_uploaded_file"]),
                language="yaml",
            )

else:
    st.error("Unknown selection.")

##################################
st.subheader("2. Data processing")
"""
The second configuration file contains all the processing methods and parameters.
In most cases, the COSMOS standard processing scheme can be used.
Different settings might be necessary for special cases.
"""
##################################


st.selectbox(
    "Select a configuration:",
    ["COSMOS Standard v1.0", "Custom configuration..."],
    key="config_processing_selected",
)

if st.session_state["config_processing_selected"] == "COSMOS Standard v1.0":

    st.session_state["config_processing_file"] = (
        Path(__file__).parent
        / "default_configuration"
        / "v1_processing_method.yaml"
    )

    st.success(
        ":material/check: Using the **{:}** configuration for data processing.".format(
            st.session_state["config_processing_selected"]
        )
    )

    with st.expander("View"):
        st.code(
            read_file(st.session_state["config_processing_file"]),
            language="yaml",
        )

elif (
    st.session_state["config_processing_selected"] == "Custom configuration..."
):
    uploaded_file = st.file_uploader(
        "Upload your configuration file",
        type={"yaml", "yml"},
        key="config_processing_uploaded",
        label_visibility="collapsed",
    )
    if uploaded_file:
        # File upload
        st.session_state["config_processing_uploaded_name"] = (
            uploaded_file.name
        )

        temp_file_path = save_uploaded_file(uploaded_file)
        atexit.register(cleanup, temp_file_path)

        st.session_state["config_processing_uploaded_file"] = temp_file_path
        st.session_state["config_processing_file"] = temp_file_path

    if st.session_state["config_processing_uploaded_file"]:
        # Already uploaded

        st.success(
            ":material/check: Using **{:}** for data processing.".format(
                st.session_state["config_processing_uploaded_name"]
            )
        )
        with st.expander("View"):
            st.code(
                read_file(st.session_state["config_processing_uploaded_file"]),
                language="yaml",
            )

else:
    st.error("Unknown selection.")

##################
st.subheader("3. Apply configuration")


# @st.cache_data(show_spinner="Checking YAML files...")
def parse_yaml_files():
    config = ConfigurationManager()
    config.load_configuration(file_path=st.session_state["config_sensor_file"])
    config.load_configuration(
        file_path=st.session_state["config_processing_file"]
    )
    st.session_state["yaml"] = ProcessWithConfig(configuration_object=config)


if (
    st.session_state["config_sensor_file"]
    and st.session_state["config_processing_file"]
):
    button_pressed = False
    if st.button(":material/settings: Check files and apply", type="primary"):
        parse_yaml_files()
        button_pressed = True
        # st.write(len(st.session_state["yaml"].sensor_config))
        st.session_state["config_already_parsed"] = False
        st.session_state["data_read_ready"] = False
        st.session_state["data_parsed"] = False
        st.session_state["data_nmdb_attached"] = False
        st.session_state["data_quality_checked"] = False
        st.session_state["data_corrections_made"] = False
        st.session_state["calibration_read_ready"] = False
        st.session_state["calibration_finished"] = False
        st.session_state["data_converted"] = False

    if st.session_state["yaml"]:
        st.success("Configuration is valid :smile:")
        st.session_state["yaml_checked"] = True

        # with st.expander("View"):
        #     st.write(st.session_state["yaml"].sensor_config.sensor_info)
    elif button_pressed:
        st.error("There is a problem with the validity of the settings.")
        st.write(st.session_state["config_sensor_file"])
        st.write(st.session_state["config_processing_file"])
        with st.expander("View"):
            st.write(st.session_state["yaml"])
            st.write(st.session_state["yaml"].sensor_config)

    if st.button("Clear cache"):
        # st.session_state.clear()
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
else:
    """
    Select two configuration files from above.
    """
