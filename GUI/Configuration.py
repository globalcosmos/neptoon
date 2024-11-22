import streamlit as st
import logging
from streamlit.logger import get_logger
import example_process.example_raw_from_yaml


def config_changed():
    st.session_state.config_changed = True


st.title("Sensor configuration file")


class StreamlitLogHandler(logging.Handler):
    def __init__(self, widget_update_func):
        super().__init__()
        self.widget_update_func = widget_update_func

    def emit(self, record):
        msg = self.format(record)
        self.widget_update_func(msg)


logger = get_logger(example_process.example_raw_from_yaml.__name__)
handler = StreamlitLogHandler(st.sidebar.empty().code)
logger.addHandler(handler)

# config_name = st.text_input(
#     "Current configuration file:",
#     value=st.session_state.config_name,
#     # key='config_name'
#     on_change=config_changed,
# )

if st.session_state.config_changed:

    col1, col2, col3 = st.columns([3, 1, 1], vertical_alignment="center")
    col1.warning(
        "There are unsaved changes to this configuration.",
        icon=":material/warning:",
    )
    if col2.button("Save", type="primary", use_container_width=True):
        st.session_state.config_name = config_name
        st.session_state.config_changed = False
        st.rerun()

    if col3.button("Reset", use_container_width=True):
        st.session_state.config = st.session_state.config_name
        st.session_state.config_changed = False
        st.rerun()

# st.divider()


uploaded_files = st.file_uploader(
    "Load existing configuration:", accept_multiple_files=True
)

if (len(uploaded_files) > 0) and (
    True
    # st.session_state.config_file != uploaded_files[0].name
):
    with st.spinner("Loading config..."):
        import example_process.example_raw_from_yaml as erfy

        st.session_state.config_file = uploaded_files[0].name

        st.session_state.config_obj = erfy.load_configuration()

if not st.session_state.config_obj is None:

    si = st.session_state.config_obj.data_hub.site_information
    # st.write(obj.data_hub.site_information)

    col1, col2 = st.columns(2, vertical_alignment="top")

    st.session_state.config_name = si.site_name
    config_name = col1.text_input(
        "Site name:",
        value=st.session_state.config_name,
        # key='config_name'
        on_change=config_changed,
    )

    # st.session_state.config_name = si.site_name
    # st.session_state.config_name = col1.text_input(
    #     "Site name", si.site_name
    # )
    lon = col1.text_input("Longitude", si.longitude)
    lat = col1.text_input("Latitude", si.latitude)
    elevation = col1.text_input("Elevation", si.elevation)
    bd = col1.text_input("Bulk density", si.dry_soil_bulk_density)
    soc = col1.text_input("Organic carbon", si.soil_organic_carbon)
    biomass = col1.text_input("Biomass", si.site_biomass)

    N0 = col2.text_input("N0", si.n0)
    cutoffrig = col2.text_input("Cutoff rigidity", si.cutoff_rigidity)
    betacoeff = col2.text_input("Beta coeff.", si.beta_coefficient)
    Lcoeff = col2.text_input("L coeff.", si.l_coefficient)
    refincneu = col2.text_input(
        "Reference incoming neutrons", si.reference_incoming_neutron_value
    )


st.write("New default configuration:")
col1, col2, col3 = st.columns(3, vertical_alignment="center")

if col1.button("CRNS Station", use_container_width=True):
    pass
if col2.button("CRNS Rover", use_container_width=True):
    pass
if col3.button("CRNS on Rails", use_container_width=True):
    pass

# st.divider()
# st.toggle(
#     "Change something",
#     # key='config_changed'
#     on_change=config_changed
# )
