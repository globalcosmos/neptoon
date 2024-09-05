import pandas as pd
from pathlib import Path
from typing import Union
from neptoon.logging import get_logger
from neptoon.data_management.site_information import SiteInformation
from neptoon.utils.general_utils import validate_and_convert_file_path

core_logger = get_logger()


class SaveAndArchiveOutputs:
    """
    Handles saving outputs from neptoons processes.

    Future Ideas:
    -------------

    - options to compress outputs (zip_output: bool = True)
    -
    """

    def __init__(
        self,
        folder_name: str,
        processed_data_frame: pd.DataFrame,
        flag_data_frame: pd.DataFrame,
        site_information: SiteInformation,
        save_folder_location: Union[str, Path] = None,
        append_yaml_hash_to_folder_name: bool = False,
        use_custom_column_names: bool = False,
        custom_column_names_dict: dict = None,
    ):
        self.folder_name = folder_name
        self.processed_data_frame = processed_data_frame
        self.flag_data_frame = flag_data_frame
        self.site_information = site_information
        self.save_folder_location = self._validate_save_folder(
            save_folder_location
        )
        self.append_yaml_hash_to_folder_name = append_yaml_hash_to_folder_name
        self.use_custom_column_names = use_custom_column_names
        self.custom_column_names_dict = custom_column_names_dict
        self.full_folder_location = None

    def _validate_save_folder(
        self,
        save_location: Union[str, Path],
    ):
        """
        Converts string path to pathlib.Path. If given path is not an
        absolute path, saves data to the current working directory.

        Parameters
        ----------
        save_location : Union[str, Path]
            The location where the data should be saved. If a location
            other than the current working directory is desired, provide
            a full path (i.e., not a relative path).

        Returns
        -------
        pathlib.Path
            The pathlib.Path object
        """
        save_path = validate_and_convert_file_path(file_path=save_location)
        if save_path is None:
            save_path = validate_and_convert_file_path(file_path=Path.cwd())
        # TODO add additional check on whether YAML hash is appendable
        return save_path

    def create_save_folder(
        self,
    ):
        """
        Creates the folder location where the data will be saved.
        """
        try:
            self.save_folder_location.mkdir()
        except FileExistsError as e:
            message = "Folder already exists."
            core_logger.info(message)

        self.full_folder_location = (
            self.save_folder_location / self.folder_name
        )
        try:
            self.full_folder_location.mkdir(parents=True)
        except FileExistsError:
            message = "Error: {e} \nFolder already exists."
            core_logger.error(message)
            print(message + " Please change the folder name and try again.")

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
        file_name,
        append_hash,
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

    def save_custom_column_names(
        self,
    ):
        """
        WIP - save custom variable names using ColumnInfo.
        """
        pass

    def save_outputs(
        self,
        nan_bad_data: bool = True,
        save_bespoke_data_frame: bool = False,
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
        file_name = self.site_information.site_name
        self.create_save_folder()
        if nan_bad_data:
            self.mask_bad_data(self.processed_data_frame)
        self.processed_data_frame.to_csv(
            (
                self.full_folder_location
                / f"{file_name}_processed_time_series.csv"
            )
        )
        self.close_and_save_data_audit_log()
