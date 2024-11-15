import pandas as pd
import math
from pathlib import Path
from typing import Union

from neptoon.logging import get_logger
from neptoon.data_audit import DataAuditLog
from neptoon.config.site_information import SiteInformation
from neptoon.utils.general_utils import validate_and_convert_file_path

core_logger = get_logger()


class SaveAndArchiveOutputs:
    """
    Handles saving the outputs from neptoons in an organised way.

    Future Ideas:
    -------------
    - options to compress outputs (zip_output: bool = True)
    - cloud connection
    - bespoke output formats
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
        """
        Attributes

        Parameters
        ----------
        folder_name : str
            Desired name for the save folder
        processed_data_frame : pd.DataFrame
            The processed time series data
        flag_data_frame : pd.DataFrame
            The flag dataframe
        site_information : SiteInformation
            The SiteInformation object.
        save_folder_location : Union[str, Path], optional
            The folder where the data should be saved. If left as None
        append_yaml_hash_to_folder_name : bool, optional
            The DataAuditLog gets converted to a hash, meaning sites
            procesed the same way share a hash. This can be appended to
            the folder automatically helping to identify sites processed
            differently, by default False
        use_custom_column_names : bool, optional
             Whether to use custom column names, by default False
        custom_column_names_dict : dict, optional
            A dictionary to convert standard neptoon names into custom a
            custom naming convention, by default None
        """
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
        return save_path

    def create_save_folder(
        self,
    ):
        """
        Creates the folder location where the data will be saved.
        """
        # Make save folder if not already there
        try:
            self.save_folder_location.mkdir()
        except FileExistsError as e:
            message = f"Error: {e} \nFolder already exists."
            core_logger.info(message)

        self.full_folder_location = (
            self.save_folder_location / self.folder_name
        )

        # Prevent overwriting station data
        try:
            self.full_folder_location.mkdir(parents=True)
        except FileExistsError as e:
            message = f"Error: {e} \nFolder already exists."
            core_logger.error(message)
            print(message + " Please change the folder name and try again.")
            raise FileExistsError

    def close_and_save_data_audit_log(
        self,
        append_hash: bool = False,
    ):
        """
        Handles closing the data audit log, producing the YAML output,
        and optionally appending a hash to the save location folder
        name.

        This function performs the following steps:
            1.  Archives and deletes the data audit log using
                DataAuditLog.archive_and_delete_log()

            2. If append_hash is True:
                a. Locates the hash.txt file in the data_audit_log
                   subfolder
                b. Reads the first 6 characters of the hash
                c. Renames the main folder to include this hash

        Parameters:
        -----------
        append_hash : bool, optional (default=False)
            If True, appends the first 6 characters of the hash from
            hash.txt to the folder name.

        """
        try:
            DataAuditLog.archive_and_delete_log(
                site_name=self.site_information.site_name,
                custom_log_location=self.full_folder_location,
            )
            if append_hash:
                new_folder_path = self.append_hash_to_folder_name(
                    self.full_folder_location
                )
                # update internal attribute
                self.full_folder_location = new_folder_path
        except Exception as e:
            message = f"Error: {e} \nCould not close DataAuditLog, presumed not created"
            core_logger.error(message)

    def append_hash_to_folder_name(
        self,
        folder_path: Path,
    ):
        """
        Appends the first 6 characters of the hash from hash.txt to the
        folder name.

        Parameters:
        -----------
        folder_path : pathlib.Path
            The path to the folder to be renamed.

        Returns:
        --------
        pathlib.Path
            The path to the renamed folder.

        Raises:
        -------
        FileNotFoundError
            If the data audit log folder or hash.txt file is not found.
        PermissionError
            If permissions to access the folder are not available.
        """
        folder_name = folder_path.name
        data_audit_folder = folder_path / "data_audit_log"

        if not data_audit_folder.exists():
            raise FileNotFoundError(
                f"Data audit log folder not found: {data_audit_folder}"
            )

        try:
            unknown_folder_name = next(data_audit_folder.glob("*/"))
            hash_file = unknown_folder_name / "hash.txt"

            if not hash_file.exists():
                raise FileNotFoundError(f"Hash file not found: {hash_file}")

            with hash_file.open("r") as f:
                contents = f.read()

            hash_append = contents[:6]
            new_folder_name = f"{folder_name}_{hash_append}"
            new_folder_path = folder_path.parent / new_folder_name
            folder_path.rename(new_folder_path)

            return new_folder_path

        except StopIteration:
            raise FileNotFoundError(
                f"No subdirectories found in {data_audit_folder}"
            )
        except PermissionError:
            raise PermissionError(
                f"Permission denied when trying to access {folder_path}"
            )
        except Exception as e:
            raise RuntimeError(
                f"An error occurred while appending hash: {str(e)}"
            )

    def mask_bad_data(
        self,
    ):
        """
        Masks out flagged data with nan values
        """
        common_columns = self.flag_data_frame.columns.intersection(
            self.processed_data_frame.columns
        )
        if len(common_columns) < len(self.processed_data_frame.columns):
            core_logger.info(
                "processed_data_frame has additional columns that "
                "will not be masked."
            )
        mask = self.flag_data_frame == "UNFLAGGED"
        masked_df = self.processed_data_frame.copy()
        masked_df[~mask] = math.nan
        return masked_df

    def save_outputs(
        self,
        nan_bad_data: bool = True,
        use_custom_column_names: bool = False,
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
        if use_custom_column_names:
            if self.custom_column_names_dict is None:
                message = (
                    "Cannot use custom column names if no "
                    "column name dictionary supplied."
                )
                core_logger.error(message)
                print(message)
                raise ValueError
        file_name = self.site_information.site_name
        self.create_save_folder()
        if nan_bad_data:
            self.processed_data_frame = self.mask_bad_data()
        self.processed_data_frame.to_csv(
            (
                self.full_folder_location
                / f"{file_name}_processed_time_series.csv"
            )
        )
        self.flag_data_frame.to_csv(
            (self.full_folder_location / f"{file_name}_flag_data_frame.csv")
        )

        self.close_and_save_data_audit_log(
            append_hash=self.append_yaml_hash_to_folder_name
        )

    # ---- TODO below this line ----
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

    def save_custom_column_names(
        self,
    ):
        """
        WIP - save custom variable names using ColumnInfo.
        """
        pass

    def save_to_cloud(
        self,
    ):
        """
        WIP - future integration with cloud services.
        """
        # TODO
        pass

    def create_pdf_output(
        self,
    ):
        """
        WIP - produce the PDF output and save in the folder.
        """
        # TODO
        pass
