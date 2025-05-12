import streamlit as st
import plotly.graph_objects as go

st.title(":material/blur_on: Neutron corrections")

if not st.session_state["data_parsed"]:
    st.warning("You need to parse the data files first.")
else:

    ##############################
    st.subheader("1. :material/trending_down: Incoming cosmic-ray reference")
    ##############################

    stations = dict(
        JUNG=(46.55, 7.98),
        SOPO=(-90, 0),
        OULU=(65.0544, 25.4681),
        PSNM=(18.59, 98.49),
        MXCO=(19.8, -99.1781),
        HRMS=(-34.43, 19.23),
    )

    @st.fragment
    def select_nm():
        colnm1, colnm2 = st.columns(2, vertical_alignment="top")

        nmdbstation_is = st.session_state[
            "yaml"
        ].process_config.correction_steps.incoming_radiation.reference_neutron_monitor.station
        nmdbstation = colnm1.pills(
            "Select a nearby high-energy neutron monitor",
            options=stations.keys(),
            default="JUNG",
        )
        if nmdbstation != nmdbstation_is:
            st.session_state[
                "yaml"
            ].process_config.correction_steps.incoming_radiation.reference_neutron_monitor.station = (
                nmdbstation
            )

        fig = go.Figure(
            go.Scattergeo(
                lat=[ll[0] for ll in stations.values()],
                lon=[ll[1] for ll in stations.values()],
                marker=dict(color="blue"),
                name="Available stations",
            )
        )
        fig.add_trace(
            go.Scattergeo(
                lat=[stations[nmdbstation][0]],
                lon=[stations[nmdbstation][1]],
                marker=dict(color="orange"),
                name="Selected station",
            )
        )
        fig.add_trace(
            go.Scattergeo(
                lat=[
                    st.session_state["yaml"].sensor_config.sensor_info.latitude
                ],
                lon=[
                    st.session_state[
                        "yaml"
                    ].sensor_config.sensor_info.longitude
                ],
                marker=dict(color="red", symbol="star"),
                name="CRNS location",
            )
        )

        # editing the marker
        fig.update_traces(marker_size=10)

        # this projection_type = 'orthographic is the projection which return 3d globe map'
        fig.update_geos(
            projection=dict(
                type="orthographic",
                rotation=dict(
                    lat=stations[nmdbstation][0], lon=stations[nmdbstation][1]
                ),  # , roll=15),
            )
        )

        # layout, exporting html and showing the plot
        fig.update_layout(
            height=200,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(
                yanchor="bottom",
                y=0.0,
            ),
        )

        colnm2.plotly_chart(fig)

    select_nm()

    # @st.cache_data(show_spinner="Downloading from NMDB...")
    def attach_nmdb(station="JUNG"):
        st.session_state["yaml"]._attach_nmdb_data(st.session_state["yaml"].data_hub)

    c1, c2 = st.columns([1, 2])

    if c1.button(":material/download: Attach cosmic-ray data", type="primary"):
        attach_nmdb(
            station=st.session_state[
                "yaml"
            ].process_config.correction_steps.incoming_radiation.reference_neutron_monitor.station
        )

    if (
        "incoming_neutron_intensity"
        in st.session_state["yaml"].data_hub.crns_data_frame.columns
    ):
        st.session_state["data_nmdb_attached"] = True
        import plotly.express as px

        (tab1,) = st.tabs([":material/show_chart: Plots"])

        tab1.plotly_chart(
            px.line(
                st.session_state["yaml"].data_hub.crns_data_frame,
                y="incoming_neutron_intensity",
            ),
            use_container_width=True,
            color_discrete_sequence=["red"],
        )

    with c2.popover(":material/help: Learn more"):
        st.markdown(
            ":material/info: The cosmic-ray reference signal is used to correct the CRNS data for incoming variation of particles, e.g. due to solar events or the solar cycle. This reference signal is measured independently by so-called neutron monitors. The signal of a neutron monitor at a similar geomagnetic cutoff-rigidity and altitude compared to the CRNS location represents the incoming flux at the CRNS site in the best way. Please visit the [NMDB station map](http://www01.nmdb.eu/nest/help.php#helpstations) for more information."
        )
        st.markdown(
            ":material/left_click: Select a nearby neutron monitor, so that its data can be downloaded from [NMDB](http://www01.nmdb.eu/nest) and attached to the CRNS data frame. "
        )

if st.session_state["data_nmdb_attached"]:

    #################################################
    st.subheader("2. :material/flag: Quality checks")
    #################################################

    c1, c2 = st.columns(2)

    # Spike detection period
    c1.number_input(
        label="Spike detection period",
        value=st.session_state[
            "yaml"
        ].process_config.neutron_quality_assessment.raw_neutrons.spike_uni_lof.periods_in_calculation,
        key="input_quality_lof_periods",
        min_value=0,
        max_value=100,
        step=1,
    )

    # Spike detection threshold
    c2.number_input(
        label="Spike detection threshold",
        value=st.session_state[
            "yaml"
        ].process_config.neutron_quality_assessment.raw_neutrons.spike_uni_lof.threshold,
        key="input_quality_lof_threshold",
        min_value=0.0,
        max_value=2.0,
        step=0.01,
    )

    @st.cache_data(show_spinner="Checking quality...")
    def make_quality_check():

        st.session_state["yaml"]._prepare_static_values(st.session_state["yaml"].data_hub)

        from neptoon.quality_control import (
            QualityAssessmentFlagBuilder,
            QualityCheck,
            QATarget,
            QAMethod,
        )

        qa_flags = QualityAssessmentFlagBuilder()
        qa_flags.add_check(
            QualityCheck(
                target=QATarget.RELATIVE_HUMIDITY,
                method=QAMethod.RANGE_CHECK,
                parameters={"min": 0, "max": 100},
            ),
            QualityCheck(
                target=QATarget.RAW_EPI_NEUTRONS,
                method=QAMethod.SPIKE_UNILOF,
                parameters={
                    "periods_in_calculation": st.session_state[
                        "input_quality_lof_periods"
                    ],
                    "threshold": st.session_state[
                        "input_quality_lof_threshold"
                    ],
                },
            ),
        )

        st.session_state["yaml"].data_hub.add_quality_flags(
            custom_flags=qa_flags
        )
        st.session_state["yaml"].data_hub.apply_quality_flags()

        st.session_state[
            "yaml"
        ].process_config.neutron_quality_assessment.raw_neutrons.spike_uni_lof.periods_in_calculation = st.session_state[
            "input_quality_lof_periods"
        ]
        st.session_state[
            "yaml"
        ].process_config.neutron_quality_assessment.raw_neutrons.spike_uni_lof.threshold = st.session_state[
            "input_quality_lof_threshold"
        ]
        st.session_state["data_quality_checked"] = True

    if st.button(":material/flag: Quality check", type="primary"):
        make_quality_check()

if st.session_state["data_quality_checked"]:
    import plotly.express as px

    tab1, tab2, tab3 = st.tabs(
        [
            ":material/Table: Raw data table",
            ":material/flag: Flagged data",
            ":material/show_chart: Plots",
        ]
    )

    tab1.dataframe(st.session_state["yaml"].data_hub.crns_data_frame)
    tab2.dataframe(st.session_state["yaml"].data_hub.flags_data_frame)
    columns_to_plot = [
        "epithermal_neutrons_raw",
        "epithermal_neutrons_cph",
    ]
    tab3.plotly_chart(
        px.line(
            st.session_state["yaml"].data_hub.crns_data_frame[columns_to_plot],
            y=columns_to_plot,
        ),
        use_container_width=True,
    )

    ###############################################################
    st.subheader("3. :material/vertical_align_center: Corrections")
    ###############################################################

    @st.fragment
    def create_correction_input():
        st.write("**3.1 Air pressure correction**")
        c1, c2 = st.columns([1, 1])
        # pressure_method = c1.segmented_control(
        #     "Method", ["Zreda et al. (2012)"], default="Zreda et al. (2012)"
        # )
        with c2.popover(":material/help: Learn more"):
            st.markdown(
                ":material/info: Air pressure represents the mass of air about the sensor. Every meter of air attenuates the cosmic radiations. The factor to correct for this effect is exponential:"
            )
            st.latex(r"C_p = e^{\beta\,(P_0-P_\text{ref})},")
            st.markdown(
                r"where $\beta$ = 0.0076 and $P_\text{ref}$ = 1013 hPa. See [Zreda et al (2012)](https://doi.org/10.5194/hess-16-4079-2012) for details."
            )

        """
        **3.2 Air humidity correction**
        """
        c1, c2 = st.columns([1, 1])

        # humidity_method = c1.segmented_control(
        #     "Method",
        #     ["Rosolem et al. (2013)"],
        #     default="Rosolem et al. (2013)",
        # )
        with c2.popover(":material/help: Learn more"):
            st.markdown(
                ":material/info: Air humidity represents the number of hydrogen atoms in the air above and around the sensor. They attenuate the cosmic radiation from above and the neutron radiation from the sides. The factor to correct for this effect is linear:"
            )
            st.latex(r"C_h = 1+\alpha\,(h-h_\text{ref}),")
            st.markdown(
                r"where $\alpha$ = 0.0054 and $h_\text{ref}$ = 0 g/m³. See [Rosolem et al (2013)](https://doi.org/10.1175/JHM-D-12-0120.1) for details."
            )

        """
        **3.3 Cosmic-ray incoming correction**
        """
        c1, c2 = st.columns([1, 1])
        # incoming_method = c1.segmented_control(
        #     "Method",
        #     ["Zreda et al. (2012)"],
        #     key="other",
        #     default="Zreda et al. (2012)",
        # )
        with c2.popover(":material/help: Learn more"):
            st.markdown(
                ":material/info: Incoming cosmic radiation varies with time and space depending on the solar activity, for instance. The reference signal is measured by neutron monitors and can be used inversely to correct the CRNS neutrons:"
            )
            st.latex(r"C_I = M_\text{ref}/M\,,")
            st.markdown(
                r"where $M$ is neutron neutron monitor data from [NMDB](http://www01.nmdb.eu/nest/) and $M_\text{ref}$ = 159 cps is a normalization factor. See [Zreda et al (2012)](https://doi.org/10.5194/hess-16-4079-2012) for details."
            )

    create_correction_input()

    @st.cache_data(show_spinner="Making corrections...")
    def make_corrections():

        from neptoon.corrections import (
            CorrectionType,
            CorrectionTheory,
        )

        st.session_state["yaml"].data_hub.select_correction(
            correction_type=CorrectionType.INCOMING_INTENSITY,
            correction_theory=CorrectionTheory.HAWDON_2014,
        )
        st.session_state["yaml"].data_hub.select_correction(
            correction_type=CorrectionType.HUMIDITY,
            correction_theory=CorrectionTheory.ROSOLEM_2013,
        )

        st.session_state["yaml"].data_hub.select_correction(
            correction_type=CorrectionType.PRESSURE,
        )

        st.session_state["yaml"].data_hub.correct_neutrons()
        st.session_state["data_corrections_made"] = True

    if st.button(
        ":material/vertical_align_center: Make corrections", type="primary"
    ):
        make_corrections()

if st.session_state["data_corrections_made"]:

    tab3, tab4, tab5 = st.tabs(
        [
            ":material/Table: Processed data table",
            ":material/show_chart: Correction factors",
            ":material/show_chart: Corrected neutrons",
        ]
    )

    tab3.dataframe(st.session_state["yaml"].data_hub.crns_data_frame)

    selected_columns_corr = [
        "atmospheric_pressure_correction",
        "humidity_correction",
        "incoming_neutron_intensity_correction",
    ]

    data_corr_factors = st.session_state["yaml"].data_hub.crns_data_frame[
        selected_columns_corr
    ]

    tab4.plotly_chart(
        px.line(data_corr_factors, y=selected_columns_corr),
        use_container_width=True,
    )

    # st.session_state["yaml"].data_hub.crns_data_frame.loc[
    #     st.session_state["yaml"].data_hub.crns_data_frame["corrected_epithermal_neutrons"] < 300,
    #     "corrected_epithermal_neutrons",
    # ] = np.nan

    # tab5.write(
    #     "For better visibility, displayed neutrons are smoothed across 24 hours."
    # )
    selected_columns_corrn = [
        "epithermal_neutrons_cph",
        "corrected_epithermal_neutrons",
    ]

    data_corr_neutrons = st.session_state["yaml"].data_hub.crns_data_frame[
        selected_columns_corrn
    ]

    tab5.plotly_chart(
        px.line(
            data_corr_neutrons,  # .rolling(24 * 4).mean(),
            y=selected_columns_corrn,
        ),
        use_container_width=True,
    )

    st.subheader(":material/airwave: Smoothing")

    # neutron_range = (
    #     st.session_state["yaml"]
    #     .data_hub.crns_data_frame["corrected_epithermal_neutrons"]
    #     .min(),
    #     st.session_state["yaml"]
    #     .data_hub.crns_data_frame["corrected_epithermal_neutrons"]
    #     .max(),
    # )

    # from neptoon.columns import ColumnInfo

    column_to_smooth = "corrected_epithermal_neutrons"  # str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)

    # st.write(column_to_smooth)

    @st.fragment
    def smooth_neutrons():

        smooth = st.slider("Smoothing window in hours", 1, 25, 1)
        column_smoothed = column_to_smooth + f"_rollingmean_{smooth}"

        st.session_state["yaml"].data_hub.smooth_data(
            column_to_smooth=column_to_smooth,
            smooth_method="rolling_mean",
            window=smooth,
        )

        show_columns = [column_to_smooth]
        if (
            column_smoothed
            in st.session_state["yaml"].data_hub.crns_data_frame
        ):
            show_columns.append(column_smoothed)

        st.plotly_chart(
            px.line(
                st.session_state["yaml"].data_hub.crns_data_frame[
                    show_columns
                ],
                y=show_columns,
                # range_y=neutron_range,
            ),
            use_container_width=True,
        )
        # st.write(st.session_state["yaml"].data_hub.crns_data_frame.columns)

    smooth_neutrons()
