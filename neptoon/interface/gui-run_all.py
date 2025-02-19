import streamlit as st


st.title(":material/web_traffic: Run all")

if not st.session_state["yaml_checked"]:
    st.warning("You need to select a configuration first.")
else:
    st.write("Run all the processing steps with a single click.")

    if st.button("Run all", type="primary"):
        with st.spinner("Running..."):
            st.session_state["yaml"].run_full_process()
            st.session_state["config_already_parsed"] = True
            st.session_state["data_read_ready"] = True
            st.session_state["data_parsed"] = True
            st.session_state["data_nmdb_attached"] = True
            st.session_state["data_quality_checked"] = True
            st.session_state["data_corrections_made"] = True
            st.session_state["calibration_read_ready"] = True
            st.session_state["calibration_finished"] = True
            st.session_state["data_converted"] = True
        st.success("Done.")
