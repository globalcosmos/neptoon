import pandas as pd
from pathlib import Path
from typing import Union
from neptoon.logging import get_logger
from neptoon.data_management.site_information import SiteInformation

core_logger = get_logger()


class SaveAndArchiveOutputs:
    """
    Handles saving outputs from neptoons processes.
    """

    def __init__(
        self,
        save_location: Union[str, Path],
        processed_data_frame: pd.DataFrame,
        flag_data_frame: pd.DataFrame,
        site_information: SiteInformation,
        zip_output: bool = False,  # option to save space
        append_yaml_hash_to_folder_name: bool = False,
        use_custom_column_names: bool = False,
        custom_column_names_dict: dict = None,
    ):
        self.save_location = save_location
        self.processed_data_frame = processed_data_frame
        self.flag_data_frame = flag_data_frame
        self.site_information = site_information
        self.zip_output = zip_output
        self.append_yaml_hash_to_folder_name = append_yaml_hash_to_folder_name
        self.use_custom_column_names = use_custom_column_names
        self.custom_column_names_dict = custom_column_names_dict

    def _validate_save_location(self):
        """
        Checks save location, if just name, saves to WD. If a folder,
        creates a PATH to that folder.

        - Check append YAML hash option. If set to yes, the folder needs
          to be renamed later.
        """
        pass

    def create_bespoke_output(
        self,
    ):
        """
        Provide an option which supports a specific type of output
        table.

        For example, creates a table which only includes meteo + SM
        data.

        """
        pass

    def close_and_save_data_audit_log(
        self,
    ):
        """
        Handles closing the data audit log and producing the YAML
        output. Additionally can be used to append the save location
        with the hashed YAML output.
        """
        # close DaL
        # create hash
        # optional - append the first 6 digits to the save folder name
        pass

    def create_pdf_output(
        self,
    ):
        """
        WIP - produce the PDF output and save in the folder.
        """
        # TODO
        pass

    def zip_data(
        self,
    ):
        """
        Will compress the data and save it.
        """
        pass

    def parse_new_yaml(
        self,
    ):
        """
        Creates a new station information YAML file and saves this in
        the folder. For example, when new averages are created from new
        data. Or when calibration produces a new N0.
        """
        # TODO
        pass

    def save_to_cloud(
        self,
    ):
        """
        WIP - future integration with cloud services.
        """
        # TODO
        pass

    def mask_bad_data(
        self,
    ):
        """
        Masks out flagged data with nan values
        """
        pass

    def create_save_location(
        self,
    ):
        """
        Creates the folder location where the data will be saved.
        """
        pass

    def save_custom_column_names(
        self,
    ):
        """
        WIP - save custom variable names using ColumnInfo.
        """
        pass

    def save_outputs(
        self,
    ):
        """
        The main function which chains the options.

        1. Create folder
        2. Mask time series
        3. Save time series
        4. Save flag df
        5. Optional: Save bespoke time series
        6. Optional: Save DAL
        7. Optional: Save Journalist
        8. Optional: rename folder
        9. Optional: compress data
        """

        pass
