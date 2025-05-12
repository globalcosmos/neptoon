import streamlit as st
from pathlib import Path
from neptoon_gui_utils import cleanup, save_uploaded_file
import atexit

st.title(":material/full_stacked_bar_chart: Read data")

if not st.session_state["yaml_checked"]:
    st.warning("You need to select a configuration first.")
else:

    ##############################
    st.subheader("1. Data source")
    ##############################

    use_raw_data = st.session_state[
        "yaml"
    ].sensor_config.raw_data_parse_options.parse_raw_data

    selected_data_type = st.segmented_control(
        "Select data type",
        ["Raw data", "Preformatted data"],
        selection_mode="single",
        default="Raw data" if use_raw_data else "Preformatted data",
    )

    if selected_data_type == "Raw data":

        st.session_state["data_raw_file"] = Path(
            st.session_state[
                "yaml"
            ].sensor_config.raw_data_parse_options.data_location
            or ""
        )

        uploaded_file = st.file_uploader(
            "Upload files",
            type={"csv", "zip"},
            key="data_raw_upload",
        )
        if uploaded_file:
            # File upload
            st.session_state["data_raw_upload_name"] = uploaded_file.name

            temp_file_path = save_uploaded_file(uploaded_file)
            atexit.register(cleanup, temp_file_path)

            st.session_state["data_raw_upload_file"] = temp_file_path
            st.session_state["data_raw_file"] = temp_file_path

        if st.session_state["data_raw_file"]:

            if not st.session_state["data_raw_file"].is_file():
                st.error(
                    "File **{:}** does not exist.".format(
                        st.session_state["data_raw_file"]
                    )
                )
                st.warning("No file selected yet. Please upload your data.")
                st.session_state["data_read_ready"] = False
            else:
                # Already uploaded
                st.success(
                    ":material/check: Using **{:}** as raw data.".format(
                        st.session_state["data_raw_file"]
                    )
                )
                st.session_state["data_read_ready"] = True

                # column_names
                st.text_input(
                    label="Column names",
                    value=", ".join(
                        st.session_state[
                            "yaml"
                        ].sensor_config.raw_data_parse_options.column_names
                        or []
                    ),
                    key="input_dataraw_column_names",
                )

                c1, c2 = st.columns(2)

                # Prefix
                c1.text_input(
                    label="Prefix",
                    value=st.session_state[
                        "yaml"
                    ].sensor_config.raw_data_parse_options.prefix,
                    key="input_dataraw_prefix",
                )

                # Suffix
                c2.text_input(
                    label="Suffix",
                    value=st.session_state[
                        "yaml"
                    ].sensor_config.raw_data_parse_options.suffix,
                    key="input_dataraw_suffix",
                )

                # skip_lines
                c1.text_input(
                    label="Skip lines",
                    value=st.session_state[
                        "yaml"
                    ].sensor_config.raw_data_parse_options.skip_lines,
                    key="input_dataraw_skip_lines",
                )

                # separator
                c2.text_input(
                    label="Separator",
                    value=st.session_state[
                        "yaml"
                    ].sensor_config.raw_data_parse_options.separator,
                    key="input_dataraw_separator",
                )

                with st.expander(
                    "More settings will be editable in future versions."
                ):
                    st.write(
                        st.session_state[
                            "yaml"
                        ].sensor_config.raw_data_parse_options,
                    )

    elif selected_data_type == "Preformatted data":

        st.session_state["data_preformatted_file"] = Path(
            st.session_state[
                "yaml"
            ].sensor_config.time_series_data.path_to_data
            or ""
        )

        uploaded_file = st.file_uploader(
            "Upload files",
            type={"csv", "zip"},
            key="data_preformatted_upload",
        )
        if uploaded_file:
            # File upload
            st.session_state["data_preformatted_upload_name"] = (
                uploaded_file.name
            )

            temp_file_path = save_uploaded_file(uploaded_file)
            atexit.register(cleanup, temp_file_path)

            st.session_state["data_preformatted_upload_file"] = temp_file_path
            st.session_state["data_preformatted_file"] = temp_file_path

        if st.session_state["data_preformatted_file"]:

            if not st.session_state["data_preformatted_file"].is_file():
                st.error(
                    "File **{:}** does not exist.".format(
                        st.session_state["data_preformatted_file"]
                    )
                )
                st.warning("No file selected yet. Please upload your data.")
                st.session_state["data_read_ready"] = False
            else:
                # Already uploaded
                st.success(
                    ":material/check: Using **{:}** as preformatted data.".format(
                        st.session_state["data_preformatted_file"]
                    )
                )
                st.session_state["data_read_ready"] = True

                c1, c2 = st.columns(2)

                # input_resolution
                c1.text_input(
                    label="Input resolution",
                    value=st.session_state[
                        "yaml"
                    ].sensor_config.time_series_data.temporal.input_resolution,
                    key="input_datapre_input_resolution",
                )

                # Output resolution
                c2.text_input(
                    label="Output resolution",
                    value=st.session_state[
                        "yaml"
                    ].sensor_config.time_series_data.temporal.output_resolution,
                    key="input_datapre_output_resolution",
                )

                # date_time_columns
                c1.text_input(
                    label="Datetime columns",
                    value=", ".join(
                        st.session_state[
                            "yaml"
                        ].sensor_config.time_series_data.key_column_info.date_time_columns
                    ),
                    key="input_datapre_date_time_columns",
                )

                # date_time_format
                c2.text_input(
                    label="Datetime format",
                    value=st.session_state[
                        "yaml"
                    ].sensor_config.time_series_data.key_column_info.date_time_format,
                    key="input_datapre_date_time_format",
                )

                with st.expander(
                    "More settings will be editable in future versions."
                ):
                    st.write(
                        st.session_state[
                            "yaml"
                        ].sensor_config.time_series_data.key_column_info,
                    )

    ################################
    st.subheader("2. :material/search_insights: Data inspection")
    ################################

    @st.cache_data(show_spinner="Creating data table...")
    def parse_data():
        # import plotly.express as px

        # with st.spinner("Creating data table..."):
        st.session_state["yaml"].data_hub =  st.session_state["yaml"]._create_data_hub(st.session_state["yaml"].sensor_config)
        data_hub = st.session_state["yaml"].data_hub
        st.write(
            "Parsed {:,.0f} lines and {:.0f} columns of data.".format(
                len(data_hub.crns_data_frame),
                len(data_hub.crns_data_frame.columns),
            )
        )
        st.session_state["data_parsed"] = True

    if st.session_state["data_read_ready"]:
        if st.button(
            ":material/read_more: Apply and parse the data!", type="primary"
        ):
            # st.write(st.session_state["yaml"].sensor_config)
            if use_raw_data:
                st.session_state[
                    "yaml"
                ].sensor_config.raw_data_parse_options.column_names = [
                    x.strip()
                    for x in st.session_state[
                        "input_dataraw_column_names"
                    ].split(",")
                ]
                st.write(
                    st.session_state[
                        "yaml"
                    ].sensor_config.raw_data_parse_options.column_names
                )
                st.session_state[
                    "yaml"
                ].sensor_config.raw_data_parse_options.prefix = st.session_state[
                    "input_dataraw_prefix"
                ]
                st.session_state[
                    "yaml"
                ].sensor_config.raw_data_parse_options.suffix = st.session_state[
                    "input_dataraw_suffix"
                ]
                st.session_state[
                    "yaml"
                ].sensor_config.raw_data_parse_options.skip_lines = int(
                    st.session_state["input_dataraw_skip_lines"]
                )
                st.session_state[
                    "yaml"
                ].sensor_config.raw_data_parse_options.separator = st.session_state[
                    "input_dataraw_separator"
                ]
            else:
                st.session_state[
                    "yaml"
                ].sensor_config.time_series_data.key_column_info.date_time_format = st.session_state[
                    "input_datapre_date_time_format"
                ]
                st.session_state[
                    "yaml"
                ].sensor_config.time_series_data.key_column_info.date_time_columns = [
                    x.strip()
                    for x in st.session_state[
                        "input_datapre_date_time_columns"
                    ].split(",")
                ]
                st.session_state[
                    "yaml"
                ].sensor_config.time_series_data.temporal.output_resolution = st.session_state[
                    "input_datapre_output_resolution"
                ]
                st.session_state[
                    "yaml"
                ].sensor_config.time_series_data.temporal.input_resolution = st.session_state[
                    "input_datapre_input_resolution"
                ]
                # st.success("Changes applied :smile:")

            parse_data()
            # st.write(st.session_state["yaml"].sensor_config)

    @st.fragment
    def make_selection_plot():
        import plotly.express as px

        tab1, tab2 = st.tabs(
            [":material/Table: Raw data table", ":material/show_chart: Plots"]
        )

        tab1.dataframe(data_hub.crns_data_frame)

        selected_columns = tab2.multiselect(
            "Which columns would you like to view?",
            options=data_hub.crns_data_frame.columns,
            default="epithermal_neutrons_cph",
        )

        filtered_data = data_hub.crns_data_frame[selected_columns]

        tab2.plotly_chart(
            px.line(filtered_data, y=selected_columns),
            use_container_width=True,
        )

    if st.session_state["data_parsed"]:
        data_hub = st.session_state["yaml"].data_hub

        make_selection_plot()
