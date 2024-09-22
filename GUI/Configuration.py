import streamlit as st

def config_changed():
    st.session_state.config_changed = True


st.title("Sensor configuration file")


config_name = st.text_input(
    "Current configuration file:",
    value=st.session_state.config_name,
    # key='config_name'
    on_change=config_changed
)

if st.session_state.config_changed:
    
    col1, col2, col3 = st.columns([3,1,1], vertical_alignment="center")
    col1.warning(
            "There are unsaved changes to this configuration.",
            icon=":material/warning:"
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


