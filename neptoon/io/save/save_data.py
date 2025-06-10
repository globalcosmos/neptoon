import pandas as pd
import math
from pathlib import Path
from typing import Union
import shutil
import json
import yaml
from typing import List
from magazine import Publish, Magazine
from neptoon.logging import get_logger
from neptoon.data_audit import DataAuditLog
from neptoon.config.configuration_input import (
    SensorInfo,
    SensorConfig,
    ProcessConfig,
)
from neptoon.utils.general_utils import validate_and_convert_file_path
from neptoon.visulisation.figures_handler import FigureHandler
from neptoon.columns import ColumnInfo

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
        sensor_info: SensorInfo,
        save_folder_location: str | Path | None = None,
        append_audit_log_hash_to_folder_name: bool = False,
        use_custom_column_names: bool = False,
        custom_column_names_dict: dict | None = None,
        append_timestamp: bool = True,
        figure_handler: FigureHandler | None = None,
        calib_df=None,
        magazine_active: bool = False,
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
        sensor_info : SensorInfo
            The SensorInfo object.
        save_folder_location : Union[str, Path], optional
            The folder where the data should be saved. If left as None
        append_audit_log_hash_to_folder_name : bool, optional
            The DataAuditLog gets converted to a hash, meaning sites
            processed the same way share a hash. This can be appended to
            the folder automatically helping to identify sites processed
            differently, by default False
        use_custom_column_names : bool, optional
             Whether to use custom column names, by default False
        custom_column_names_dict : dict, optional
            A dictionary to convert standard neptoon names into custom a
            custom naming convention, by default None
        append_timestamp: bool, optional, by default True
            Whether to append a timestamp to the folder name when
            saving.
        """
        self.folder_name = folder_name
        self.processed_data_frame = processed_data_frame
        self.flag_data_frame = flag_data_frame
        self.sensor_info = sensor_info
        self.save_folder_location = self._validate_save_folder(
            save_folder_location
        )
        self.append_audit_log_hash_to_folder_name = (
            append_audit_log_hash_to_folder_name
        )
        self.use_custom_column_names = use_custom_column_names
        self.custom_column_names_dict = custom_column_names_dict
        self.append_timestamp = append_timestamp
        self.full_folder_location = None
        self.figure_handler = figure_handler
        self.calib_df = calib_df
        self.magazine_active = magazine_active

    def _validate_save_folder(
        self,
        save_location: str | Path | None,
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

        if self.append_timestamp:
            from datetime import datetime

            # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        else:
            timestamp = ""

        new_folder_name = self.folder_name + "_" + timestamp

        self.full_folder_location = self.save_folder_location / new_folder_name

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
                site_name=self.sensor_info.name,
                custom_log_location=self.full_folder_location,
            )
            if append_hash:
                new_folder_path = self.append_hash_to_folder_name(
                    self.full_folder_location
                )
                # update internal attribute
                self.full_folder_location = new_folder_path
        except AttributeError as e:
            message = f"{e}: DataAuditLog not present - skipping archive step"
            core_logger.info(message)
        except Exception as e:
            message = f"Unexpected error in DataAuditLog archiving: {e}"
            core_logger.error(message)

    def append_hash_to_folder_name(
        self,
        folder_path: Path | None,
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

    def _save_figures(self):
        """
        Handles saving figures
        """

        figure_metadata = [
            fig_md for fig_md in self.figure_handler.temp_handler.get_figures()
        ]

        figure_folder = self.full_folder_location / "figures"
        figure_folder.mkdir(parents=True, exist_ok=True)
        for figure in figure_metadata:
            try:
                dest = figure_folder / f"{figure.name}.png"
                shutil.copy2(figure.path, dest)
            except FileNotFoundError as err:
                message = f"{figure.name} not found: {err}."
                core_logger.error(message)

    def _update_sensor_info(
        self,
        fields_to_check: List[str] = [
            "beta_coefficient",
            "mean_pressure",
        ],
        beta_col=str(ColumnInfo.Name.BETA_COEFFICIENT),
        mean_press_col=str(ColumnInfo.Name.MEAN_PRESSURE),
    ):
        """
        Updates SensorInfo if values where calulated during processing.

        Parameters
        ----------
        fields_to_check : List[str], optional
            A list of values in SensorInfo to check, by default [
            "beta_coefficient", "l_coefficient", "mean_pressure", ]
        beta_col : str, optional
            Beta Coefficient column name, by default
            str(ColumnInfo.Name.BETA_COEFFICIENT)
        mean_press_col : str, optional
            mean pressure column name, by default
            str(ColumnInfo.Name.MEAN_PRESSURE)
        """
        missing_fields = [
            field
            for field in fields_to_check
            if getattr(self.sensor_info, field) is None
        ]
        if (
            beta_col in self.processed_data_frame.columns
            and "beta_coefficient" in missing_fields
        ):
            beta_coeff = self.processed_data_frame[beta_col].iloc[0]
            self.sensor_info.beta_coefficient = round(beta_coeff, 4)
        if (
            mean_press_col in self.processed_data_frame.columns
            and "mean_pressure" in missing_fields
        ):
            mean_pressure = self.processed_data_frame[mean_press_col].iloc[0]
            self.sensor_info.mean_pressure = round(mean_pressure, 2)

    def _save_pdf(self, location: Path | str):
        """
        Exports the pdf built using magazine to the save folder.

        Parameters
        ----------
        location : Path
            The Path to the folder where the pdf is saved
        """
        if self.magazine_active:
            name = self.sensor_info.name
            save_location = location / f"Report-{name}.pdf"
            with Publish(str(save_location), f"{name} data") as pdf:
                pdf.add_topic("Neutron Correction")
                pdf.add_figure("Neutron Correction")
                pdf.add_topic("NMDB")
                pdf.add_figure("NMDB")
                pdf.add_topic("Soil Moisture")
                pdf.add_figure("Soil Moisture")
                pdf.add_topic("Atmospheric Conditions")
                pdf.add_figure("Atmospheric Conditions")
                pdf.add_topic("Calibration")
                pdf.add_figure("Calibration")
                pdf.add_topic("Data Preparation")
                pdf.add_figure("Data Preparation")

    def save_data_frames(self, file_name):
        """
        Saves various data frames as .csv files.
        """
        data_folder = self.full_folder_location / "data"
        data_folder.mkdir()
        self.processed_data_frame.to_csv(
            data_folder / f"{file_name}_processed_data.csv"
        )
        self.flag_data_frame.to_csv(data_folder / f"{file_name}_flags.csv")
        if self.calib_df is not None:
            self.calib_df.to_csv(data_folder / f"{file_name}_calibration.csv")

    def save_outputs(
        self,
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
        file_name = self.sensor_info.name
        self.create_save_folder()
        self.save_data_frames(file_name=file_name)
        if self.figure_handler:
            self._save_figures()
        self._update_sensor_info()
        if Magazine.active:
            self._save_pdf(location=self.full_folder_location)
        self.close_and_save_data_audit_log(
            append_hash=self.append_audit_log_hash_to_folder_name
        )

    # ---- TODO below this line ----

    def save_custom_column_names(
        self,
    ):
        """
        WIP - save custom variable names using ColumnInfo.
        """
        pass


class ConfigSaver:
    """
    Saves the SensorConfig object as a yaml file.
    """

    def __init__(
        self,
        save_folder_location: Path | str,
        config: SensorConfig,
    ):
        self.save_folder_location = save_folder_location
        self.config = config

    def save(
        self,
    ):
        """
        Convert a Pydantic model to YAML file and save it.
        """
        if isinstance(self.config, SensorConfig):
            save_location = (
                self.save_folder_location / "updated_sensor_config.yaml"
            )
        if isinstance(self.config, ProcessConfig):
            save_location = (
                self.save_folder_location / "updated_process_config.yaml"
            )
        json_str = self.config.model_dump_json()
        data = json.loads(json_str)

        config_str = yaml.safe_dump(
            data,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
            default_style=None,
        )

        Path(save_location).write_text(config_str)
