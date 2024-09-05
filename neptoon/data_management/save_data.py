import pandas as pd
from pathlib import Path
from typing import Union
from neptoon.logging import get_logger
from neptoon.data_management.site_information import SiteInformation


core_logger = get_logger()


def validate_and_convert_file_path(
    file_path: Union[str, Path, None],
    base: Union[str, Path] = "",
) -> Path:
    """
    Used when initialising the object. If a string is given as a
    data_location, it is converted to a pathlib.Path object. If a
    pathlib.Path object is given this is returned. Other types will
    cause an error.

    Parameters
    ----------
    data_location : Union[str, Path]
        The data_location attribute from initialisation.

    Returns
    -------
    pathlib.Path
        The data_location as a pathlib.Path object.

    Raises
    ------
    ValueError
        Error if string or pathlib.Path given.
    """

    if file_path is None:
        return None
    if isinstance(file_path, str):
        new_file_path = Path(file_path)
        if new_file_path.is_absolute():
            return new_file_path
        else:
            return base / Path(file_path)
    elif isinstance(file_path, Path):
        if file_path.is_absolute():
            return file_path
        else:
            return base / file_path
    else:
        message = (
            "data_location must be of type str or pathlib.Path. \n"
            f"{type(file_path).__name__} provided, "
            "please change this."
        )
        core_logger.error(message)
        raise ValueError(message)


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
