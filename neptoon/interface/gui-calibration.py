import streamlit as st
from pathlib import Path
from neptoon_gui_utils import cleanup, save_uploaded_file
import atexit

st.title(":material/adjust: Calibration")

if not st.session_state["data_corrections_made"]:
    st.warning("You need to process all neutron corrections first.")
else:

    st.write(
        "In order to find the $N_0$ parameter, a CRNS probe needs to be calibrated on ground truth data, e.g., soil samples or TDR time serieses.",
        "You can upload your calibration dataset here. In a future version, you may input your otherwise determined average soil moisture.",
    )

    st.session_state["calibration_file"] = Path(
        st.session_state["yaml"].sensor_config.calibration.location or ""
    )

    uploaded_file = st.file_uploader(
        "Upload files",
        type={"csv"},
        key="calibration_upload",
    )
    if uploaded_file:
        # File upload
        st.session_state["calibration_upload_name"] = uploaded_file.name

        temp_file_path = save_uploaded_file(uploaded_file)
        atexit.register(cleanup, temp_file_path)

        st.session_state["calibration_upload_file"] = temp_file_path
        st.session_state["calibration_file"] = temp_file_path

    if st.session_state["calibration_file"]:

        if not st.session_state["calibration_file"].is_file():
            st.error(
                "File **{:}** does not exist.".format(
                    st.session_state["calibration_file"]
                )
            )
            st.warning("No file selected yet. Please upload your data.")
            st.session_state["calibration_read_ready"] = False
        else:
            # Already uploaded
            st.success(
                ":material/check: Using **{:}** as calibration data.".format(
                    st.session_state["calibration_file"]
                )
            )
            st.session_state["yaml"].sensor_config.calibration.location = (
                st.session_state["calibration_file"]
            )
            st.session_state["calibration_read_ready"] = True

            import pandas as pd

            st.session_state["yaml"].data_hub.calibration_samples_data = (
                pd.read_csv(st.session_state["calibration_file"])
            )
            st.dataframe(
                st.session_state["yaml"].data_hub.calibration_samples_data
            )

if st.session_state["calibration_read_ready"]:

    ##############################################
    st.subheader(":material/adjust: Calibration")
    ##############################################

    @st.cache_data(show_spinner="Calibrating")
    def make_calibration():
        st.session_state["yaml"]._calibrate_data(st.session_state["yaml"].data_hub, st.session_state["yaml"].sensor_config)
        st.session_state["calibration_finished"] = True

    if st.button("Calibrate!", type="primary"):
        make_calibration()

if st.session_state["calibration_finished"]:
    df_calibrated = st.session_state[
        "yaml"
    ].data_hub.calibrator.return_calibration_results_data_frame()
    st.write(df_calibrated)
    str_no = "Estimated: $N_0 = {:.0f}$ ".format(
        st.session_state["yaml"].sensor_config.sensor_info.N0,
    )
    if len(df_calibrated["optimal_N0"].dropna() > 1):
        str_std = "$\pm {:.0f}$".format(
            df_calibrated["optimal_N0"].std(),
        )
    else:
        str_std = ""
    str_unit = " cph."
    st.write(str_no + str_std + str_unit)
    # st.write(st.session_state["yaml"].data_hub.crns_data_frame.columns)
