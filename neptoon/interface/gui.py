import streamlit as st
from pathlib import Path
from magazine import Magazine

Magazine.active = True
# Icons: https://fonts.google.com/icons?icon.set=Material+Symbols&icon.style=Rounded
current_path = Path(__file__).parent

st.set_page_config(
    page_title="Neptoon GUI",
    page_icon="assets/neptoon-logo-ball.svg",
)

st.logo(
    image=current_path / "assets" / "neptoon-logo.svg",
    link="https://codebase.helmholtz.cloud/cosmos/neptoon_documentation",
    # icon_image=LOGO_URL_SMALL,
)

pages = [
    st.Page(
        "gui-configuration.py",
        title="Configuration",
        icon=":material/settings:",
    ),
    st.Page(
        "gui-site_information.py",
        title="Site information",
        icon=":material/info:",
    ),
    st.Page(
        "gui-read_data.py",
        title="Read data",
        icon=":material/full_stacked_bar_chart:",
    ),
    st.Page(
        "gui-neutron_corrections.py",
        title="Neutron corrections",
        icon=":material/blur_on:",
    ),
    st.Page(
        "gui-calibration.py",
        title="Calibration",
        icon=":material/adjust:",
    ),
    st.Page(
        "gui-water.py",
        title="Water",
        icon=":material/water_drop:",
    ),
    st.Page(
        "gui-run_all.py",
        title="Run all",
        icon=":material/web_traffic:",
    ),
    st.Page(
        "gui-export.py",
        title="Export",
        icon=":material/save:",
    ),
]

# Initialize sharable session variables
shared_session_variables = dict(
    config_sensor_selected="Custom configuration...",
    config_sensor_file=None,
    config_sensor_uploaded_file=None,
    config_sensor_uploaded_name="",
    config_processing_selected="COSMOS Standard v1.0",
    config_processing_file=None,
    config_processing_uploaded_file=None,
    config_processing_uploaded_name="",
    config_already_parsed=False,
    yaml=None,
    yaml_checked=False,
    data_preformatted_file=None,
    data_preformatted_upload_file=None,
    data_preformatted_upload_name="",
    data_preraw_file=None,
    data_preraw_upload_file=None,
    data_preraw_upload_name="",
    data_read_ready=False,
    data_parsed=False,
    data_nmdb_attached=False,
    data_quality_checked=False,
    data_corrections_made=False,
    calibration_file=None,
    calibration_upload_file=None,
    calibration_upload_name="",
    calibration_read_ready=False,
    calibration_finished=False,
    data_converted=False,
)
for var in shared_session_variables:
    if var not in st.session_state:
        st.session_state[var] = shared_session_variables[var]
    st.session_state[var] = st.session_state[var]  # keeps widget keys alive
# st.session_state[var] = "Custom configuration..."


st.sidebar.image(
    image=current_path / "assets" / "neptoon-affils.svg",
    use_container_width=False,
    width=70,
)


# lets turn on the reporting system for our data


pg = st.navigation(pages)
pg.run()
