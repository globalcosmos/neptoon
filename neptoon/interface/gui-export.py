import streamlit as st
from pathlib import Path

st.title(":material/save: Export")


if not st.session_state["data_corrections_made"]:
    st.warning("You need to process all neutron corrections first.")

if st.session_state["data_converted"]:

    @st.cache_data(show_spinner="Making figures...")
    def make_figures():
        st.session_state["yaml"].data_hub.create_figures(create_all=True)

    @st.cache_data(show_spinner="Save data...")
    def save_data():
        st.session_state["yaml"].data_hub.save_data()

    c11, c12, c13, c14 = st.columns(4)
    if c11.button("Make figures", type="primary"):
        make_figures()

    c21, c22, c23, c24 = st.columns(4)
    if c21.button("Save data", type="primary"):
        save_data()

    import glob

    sensor_name = st.session_state["yaml"].sensor_config.sensor_info.name
    matching_folders = glob.glob("{:}_*".format(sensor_name))
    if len(matching_folders) > 0:
        matching_numbers = [
            int(x[x.index("_") + 1 :]) for x in matching_folders
        ]
        latest_folder = "{:}_{:}".format(sensor_name, matching_numbers[-1])
        # st.write(latest_folder)

        pdf_report = "{:}/Report-{:}.pdf".format(latest_folder, sensor_name)
        if Path(pdf_report).is_file():
            with open(pdf_report, "rb") as file:
                btn = c12.download_button(
                    label=":material/description: PDF Report",
                    data=file,
                    file_name="Report-{:}.pdf".format(sensor_name),
                    mime="application/pdf",
                )

        csv_calibration = "{:}/data/{:}_calibration.csv".format(
            latest_folder, sensor_name
        )
        if Path(csv_calibration).is_file():
            with open(pdf_report, "rb") as file:
                btn = c22.download_button(
                    label=":material/table: Calibration data",
                    data=file,
                    file_name="{:}_calibration.csv".format(sensor_name),
                    mime="text/csv",
                )

        csv_flags = "{:}/data/{:}_flags.csv".format(latest_folder, sensor_name)
        if Path(csv_flags).is_file():
            with open(csv_flags, "rb") as file:
                btn = c23.download_button(
                    label=":material/table: Flag data",
                    data=file,
                    file_name="{:}_flags.csv".format(sensor_name),
                    mime="text/csv",
                )

        csv_processed_data = "{:}/data/{:}_processed_data.csv".format(
            latest_folder, sensor_name
        )
        if Path(csv_processed_data).is_file():
            with open(csv_processed_data, "rb") as file:
                btn = c24.download_button(
                    label=":material/table: Processed data",
                    data=file,
                    file_name="{:}_processed_data.csv".format(sensor_name),
                    mime="text/csv",
                )

        import os

        st.subheader("Image files")

        # Define the folder path
        image_folder = "{:}/figures/".format(latest_folder)

        # Get a list of image files
        image_files = [
            f for f in os.listdir(image_folder) if f.endswith(".png")
        ]

        for image in image_files:
            st.image(
                os.path.join(image_folder, image),
                caption=image,
                use_container_width=True,
            )
