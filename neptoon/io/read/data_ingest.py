import pandas as pd
import numpy as np
import tarfile
import tempfile
import atexit
from dataclasses import dataclass
from enum import Enum, auto
import zipfile
import io
from pathlib import Path
from typing import Union, Literal, List, Optional

from neptoon.logging import get_logger
from neptoon.utils.general_utils import (
    validate_and_convert_file_path,
    parse_resolution_to_timedelta,
)
from neptoon.columns import ColumnInfo
from neptoon.config.configuration_input import (
    ConfigurationManager,
)
from neptoon.utils import find_temporal_resolution_seconds

core_logger = get_logger()


class FileCollectionConfig:
    """
    Configuration class for file collection and parsing settings.

    This class holds all the necessary parameters for locating, reading,
    and parsing data files, providing a centralized configuration for
    the data ingestion process.
    """

    def __init__(
        self,
        path_to_config: Union[str, Path] = None,
        data_location: Union[str, Path] = None,
        column_names: list = None,
        prefix="",
        suffix="",
        encoding="cp850",
        skip_lines: int = 0,
        separator: str = ",",
        decimal: str = ".",
        skip_initial_space: bool = True,
        parser_kw_strip_left: bool = True,
        parser_kw_digit_first=True,
        starts_with: any = "",
        multi_header: bool = False,
        strip_names: bool = True,
        remove_prefix: str = "//",
    ):
        """
        Initial parameters for data collection and merging

        Parameters
        ----------
        path_to_config : Union[str, Path]
            The location of the sensor configuration file. Can be either
            a string or Path object
        data_location : Union[str, Path]
            The location of the data files. Can be either a string or
            Path object
        column_names : list, optional
            List of column names for the data, by default None
        prefix : str, optional
            Start of file name for file filtering, by default None
        suffix : str, optional
            End of file name - used for file filtering, by default None
        encoding : str, optional
            Encoder used for file encoding, by default "cp850"
        skip_lines : int, optional
            Whether lines should be skipped when parsing files, by
            default 0
        seperator : str, optional
            Column seperator in the files, by default ","
        decimal : str, optional
            The default decimal character for floating point numbers ,
            by default "."
        skip_initial_space : bool, optional
            Whether to skip intial space when creating dataframe, by
            default True
        parser_kw : dict, optional
            Dictionary with parser values to use when parsing data, by
            default dict(
                strip_left=True, digit_first=True, )
        starts_with : any, optional
            String that headers must start with, by default ""
        multi_header : bool, optional
            Whether to look for multiple header lines, by default False
        strip_names : bool, optional
            Whether to strip whitespace from column names, by default
            True
        remove_prefix : str, optional
            Prefix to remove from column names, by default "//"
        """
        self._path_to_config = validate_and_convert_file_path(
            file_path=path_to_config
        )
        self._data_location = validate_and_convert_file_path(
            file_path=data_location,
            # base=(
            #     self.path_to_config.parent
            #     if self.path_to_config is not None
            #     else ""
            # ),
        )
        self._data_source = None
        self.column_names = column_names
        self.prefix = prefix
        self.suffix = suffix
        self.encoding = encoding
        self.skip_lines = skip_lines
        self.parser_kw_strip_left = parser_kw_strip_left
        self.parser_kw_digit_first = parser_kw_digit_first
        self._separator = separator
        self._decimal = decimal
        self.skip_initial_space = skip_initial_space
        self.starts_with = starts_with
        self.multi_header = multi_header
        self.strip_names = strip_names
        self._remove_prefix = remove_prefix

        self._determine_source_type()

    @property
    def path_to_config(self):
        return self._path_to_config

    @path_to_config.setter
    def path_to_config(self, new_path):
        self._path_to_config = validate_and_convert_file_path(new_path)

    @property
    def data_location(self):
        return self._data_location

    @data_location.setter
    def data_location(self, new_location):
        self._data_location = validate_and_convert_file_path(
            new_location,
        )
        self._determine_source_type()

    @property
    def data_source(self):
        return self._data_source

    @property
    def separator(self):
        return self._separator

    @separator.setter
    def separator(self, value):
        if isinstance(value, str):
            self._separator = value.replace("'", "").replace('"', "")
        else:
            message = f"{value} is not a string type. It must be a string"
            core_logger.error(message)
            raise ValueError(message)

    @property
    def remove_prefix(self):
        return self._remove_prefix

    @remove_prefix.setter
    def remove_prefix(self, value):
        if isinstance(value, str):
            self._remove_prefix = value.replace("'", "").replace('"', "")
        else:
            message = f"{value} is not a string type. It must be a string"
            core_logger.error(message)
            raise ValueError(message)

    @property
    def decimal(self):
        return self._decimal

    @decimal.setter
    def decimal(self, value):
        if isinstance(value, str):
            self._decimal = value.replace("'", "").replace('"', "")
        else:
            message = f"{value} is not a string type. It must be a string"
            core_logger.error(message)
            raise ValueError(message)

    def _determine_source_type(self):
        """
        Checks if the folder is a normal folder or an archive and sets
        the internal attribute reflecting this.
        """
        if self._data_location is None:
            self._data_source = None
            return
        if self._data_location.is_dir():
            self._data_source = "folder"
            core_logger.info("Extracting data from a folder")
            return

        try:
            if tarfile.is_tarfile(self._data_location):
                self._data_source = "tarfile"
                core_logger.info("Extracting data from a tarfile")
                self.dump_tar()

            elif zipfile.is_zipfile(self._data_location):
                self._data_source = "zipfile"
                core_logger.info("Extracting data from a zipfile")
                self.dump_zip()

            else:
                self._data_source = None
                core_logger.info("Cannot determine data source type")

        except (tarfile.TarError, zipfile.BadZipFile) as e:
            self._data_source = None
            core_logger.error(f"Failed to extract archive: {str(e)}")
            raise

        else:
            self._data_source = None
            core_logger.info("Cannot determine data source type")

    def dump_tar(self):
        """Create temporary directory and extract"""
        self._temp_dir_obj = tempfile.TemporaryDirectory()
        temp_dir = Path(self._temp_dir_obj.name)
        zip_dirname = Path(self._data_location).stem
        with tarfile.open(self._data_location) as tar:
            tar.extractall(path=temp_dir)
        extracted_items = list(temp_dir.iterdir())
        if extracted_items and extracted_items[0].is_dir():
            self._data_location = temp_dir / zip_dirname
        else:
            self._data_location = temp_dir
        self._temp_dir = temp_dir
        self._original_location = self._data_location
        atexit.register(self._cleanup_temp)

    def dump_zip(self):
        """Create temporary directory and extract"""

        self._temp_dir_obj = tempfile.TemporaryDirectory()
        temp_dir = Path(self._temp_dir_obj.name)
        zip_dirname = Path(self._data_location).stem

        with zipfile.ZipFile(self._data_location) as zip_ref:
            zip_ref.extractall(temp_dir)

        extracted_items = list(temp_dir.iterdir())
        if extracted_items and extracted_items[0].is_dir():
            self._data_location = temp_dir / zip_dirname
        else:
            self._data_location = temp_dir

        self._original_location = self._data_location
        atexit.register(self._cleanup_temp)

    def _cleanup_temp(self):
        """
        Cleanup temporary directory. Registered with atexit for
        automatic cleanup.
        """
        try:
            if hasattr(self, "_temp_dir_obj"):
                self._temp_dir_obj.cleanup()
                delattr(self, "_temp_dir_obj")
        except Exception as e:
            # Just log any cleanup errors during exit
            core_logger.warning(f"Failed to cleanup temporary directory: {e}")

    def build_from_config(
        self,
        path_to_config: Optional[Union[Path, str]] = None,
    ):
        """
        Imports the attributes for the instance of FileCollectionConfig
        from a pre-configured YAML file

        Parameters
        ----------
        path_to_config : Union[Path, str], optional
            Path to the sensor configuration file, by default None

        Raises
        ------
        ValueError
            If no suitable path given
        """
        if path_to_config is None and self._path_to_config is None:
            message = "No path given for config file"
            core_logger.error(message)
            raise ValueError(message)
        else:
            path = (
                path_to_config
                if path_to_config is not None
                else self._path_to_config
            )
            path = validate_and_convert_file_path(path)

        internal_config = ConfigurationManager()
        internal_config.load_configuration(
            file_path=path,
        )
        sensor_config = internal_config.get_config("sensor")

        self.data_location = sensor_config.raw_data_parse_options.data_location
        self.column_names = sensor_config.raw_data_parse_options.column_names
        self.prefix = sensor_config.raw_data_parse_options.prefix
        self.suffix = sensor_config.raw_data_parse_options.suffix
        self.encoding = sensor_config.raw_data_parse_options.encoding
        self.skip_lines = sensor_config.raw_data_parse_options.skip_lines
        self.parser_kw_strip_left = (
            sensor_config.raw_data_parse_options.parser_kw.strip_left
        )
        self.parser_kw_digit_first = (
            sensor_config.raw_data_parse_options.parser_kw.digit_first
        )
        self.separator = sensor_config.raw_data_parse_options.separator
        self.decimal = sensor_config.raw_data_parse_options.decimal
        self.skip_initial_space = (
            sensor_config.raw_data_parse_options.skip_initial_space
        )
        self.starts_with = sensor_config.raw_data_parse_options.starts_with
        self.multi_header = sensor_config.raw_data_parse_options.multi_header
        self.strip_names = sensor_config.raw_data_parse_options.strip_names
        self.remove_prefix = sensor_config.raw_data_parse_options.remove_prefix


class ManageFileCollection:
    """
    Manages the collection of files in preperation for parsing them into
    a DataFrame for the CRNSDataHub.

    Example:
    --------
    >>> config = FileCollectionConfig(data_location="/path/to/folder")
    >>> file_manager = ManageFileCollection(config)
    >>> file_manager.get_list_of_files()
    >>> file_manager.filter_files()
    """

    def __init__(
        self,
        config: FileCollectionConfig,
        files: List = None,
    ):
        """
        Initial parameters

        Parameters
        ----------
        config : FileCollectionConfig[str, Path]
            The config file holding key information for collection
        files : List
            Placeholder for files

        """
        self.config = config
        self.files = files

    def get_list_of_files(self):
        """
        Lists the files found at the data_location and assigns these to
        the file attribute.
        """
        files = []
        if self.config.data_location.is_dir():
            try:
                item_list = self.config.data_location.glob("**/*")
                files = [x.name for x in item_list if x.is_file()]

            except FileNotFoundError as fnf_error:
                message = (
                    f"! Folder not found: {self.config.data_location}."
                    f"Error: {fnf_error}"
                )
                core_logger.error(message)
                raise
            except Exception as err:
                message = (
                    f"! Error accessing folder {self.config.data_location}."
                    f" Error: {err}"
                )
                core_logger.error(message)
                raise

        self.files = files

    def filter_files(
        self,
    ):
        """
        Filters the files found in the data location using the prefix or
        suffix given during initialisation. Both of these default to
        None.

        This method updates the `files` attribute of the class with the
        filtered list.

        TODO maybe add regexp or * functionality
        """

        files_filtered = [
            filename
            for filename in self.files
            if filename.startswith(self.config.prefix)
        ]

        # End with ...
        files_filtered = [
            filename
            for filename in files_filtered
            if filename.endswith(self.config.suffix)
        ]

        # raise error when no files are found
        if len(files_filtered) == 0:
            message = (
                f"No files found in {self.config.data_location} "
                f"with prefix '{self.config.prefix}' and suffix '{self.config.suffix}'."
            )
            core_logger.error(message)
            raise FileNotFoundError(message)

        self.files = files_filtered

    def create_file_list(self):
        """
        Create clean file list
        """
        self.get_list_of_files()
        self.filter_files()


class ParseFilesIntoDataFrame:
    """
    Parses raw files into a single pandas DataFrame.

    This class takes instances of ManageFileCollection and
    FileCollectionConfig to process and combine multiple data files into
    a single DataFrame, handling various file formats and parsing
    configurations.

    Example
    -------
    >>> config = FileCollectionConfig(data_location='/path/to/data/folder/')
    >>> file_manager = ManageFileCollection(config=config)
    >>> file_parser = ParseFilesIntoDataFrame(file_manager, config)
    >>> df = file_parser.make_dataframe()
    """

    def __init__(
        self,
        file_manager: ManageFileCollection,
        config: FileCollectionConfig,
    ):
        """
        Initialisation files.

        Parameters
        ----------
        file_manager : ManageFileCollection
            An instance fo the ManageFileCollection class
        config : FileCollectionConfig
            The config file containing information to support
            processing.

        """
        self.file_manager = file_manager
        self.config = config

    def make_dataframe(
        self,
        column_names=None,
    ) -> pd.DataFrame:
        """
        Merges, parses and converts data it to a single DataFrame.

        Parameters
        ----------
        column_names : list, optional
            Can supply custom column_names for saving file, by default
            None

        Returns
        -------
        pd.DataFrame
            DataFrame with all data
        """
        if column_names is None:
            column_names = self.config.column_names

        if column_names is None:
            column_names = self._infer_column_names()

        data_str = self._merge_files()

        data = pd.read_csv(
            io.StringIO(data_str),
            names=column_names,
            encoding=self.config.encoding,
            skiprows=self.config.skip_lines,
            skipinitialspace=self.config.skip_initial_space,
            sep=self.config.separator,
            decimal=self.config.decimal,
            on_bad_lines="skip",  # ignore all lines with bad columns
            dtype=object,  # Allows for reading strings
            index_col=False,
        )
        return data

    def _merge_files(
        self,
    ) -> str:
        """
        Reads all selected files and merges them into a single large
        data string.

        This method processes each file using the `_process_file` method
        and combines the results.

        Returns
        -------
        str
            A single large string containing all data lines
        """
        return "".join(
            self._process_file(filename)
            for filename in self.file_manager.files
        )

    def _read_file_content(
        self,
        file,
    ) -> str:
        """
        Reads the file content by parsing each line. Skips lines based
        on config file selection.

        Parameters
        ----------
        file : *
            The file to parse.

        Returns
        -------
        str
            string representation of file
        """
        for _ in range(self.config.skip_lines):
            next(file)
        return "".join(self._parse_file_line(line) for line in file)

    def _process_file(
        self,
        filename,
    ) -> str:
        """
        Processes a single file and extracts its content into a string.

        Parameters
        ----------
        filename : str
            The name of the file to process

        Returns
        -------
        str
            A string containing the processed data from the file
        """
        with self._open_file(filename, self.config.encoding) as file:
            return self._read_file_content(file)

    def _open_file(
        self,
        filename: str,
        encoding: str,
    ):
        """
        Opens an individual file from either a folder, zipfile, or
        tarfile.

        Parameters
        ----------
        filename : str
            The filename to be opened
        encoding : str
            Encoding of the file

        Returns
        -------
        file
            returns the open file
        """
        try:
            return open(
                self.config.data_location / filename,
                encoding=encoding,
            )
        except Exception as e:
            raise IOError(f"Error opening file {filename}: {str(e)}")

    def _parse_file_line(
        self,
        line: str,
    ) -> str:
        """
        Parses a single line

        Parameters
        ----------
        line : str
            line of potential dat

        Returns
        -------
        str
            a valid line or an empty string
        """

        ###

        if isinstance(line, bytes) and self.config.encoding != "":
            line = line.decode(self.config.encoding, errors="ignore")

        if self.config.parser_kw_strip_left:
            line = line.lstrip()

        # If the line starts with a number, it likely is actual data
        if self.config.parser_kw_digit_first and not line[:1].isdigit():
            return ""

        return line

    def _infer_column_names(
        self,
    ) -> list:
        """
        Reads a file and tries to infer the column headers.

        Parameters
        ----------
        filename : str
            name of the file to read

        Returns
        -------
        list
            List of column names
        """

        # Open file in either folder or archive
        with self._open_file(
            self.file_manager.files[0], self.config.encoding
        ) as file:

            for _ in range(self.config.skip_lines):
                next(file)

            headers = []
            for line in file:

                if isinstance(line, bytes) and self.config.encoding != "":
                    line = line.decode(self.config.encoding, errors="ignore")

                if self.config.separator in line:
                    # headers must contain at least one separator

                    if line.startswith(self.config.starts_with):
                        # headers must start with certain letters
                        # Uses the first line if no letter given

                        headers.append(line)

                        if not self.config.multi_header:
                            # Stops after first found header, else browse the whole file
                            break

        # Join multiheaders and create a joint list
        header_line = self.config.separator.join(headers)
        header_list = header_line.split(self.config.separator)
        if self.config.strip_names:
            header_list = [s.strip() for s in header_list]
        if self.config.remove_prefix != "":
            header_list = [
                s.removeprefix(self.config.remove_prefix) for s in header_list
            ]
        return header_list


class InputColumnDataType(Enum):
    DATE_TIME = auto()
    PRESSURE = auto()
    TEMPERATURE = auto()
    RELATIVE_HUMIDITY = auto()
    EPI_NEUTRON_COUNT = auto()
    THERM_NEUTRON_COUNT = auto()
    ELAPSED_TIME = auto()


class NeutronCountUnits(Enum):
    ABSOLUTE_COUNT = auto()
    COUNTS_PER_HOUR = auto()
    COUNTS_PER_SECOND = auto()


class PressureUnits(Enum):
    PASCALS = auto()
    HECTOPASCALS = auto()
    KILOPASCALS = auto()


class MergeMethod(Enum):
    MEAN = auto()
    PRIORITY = auto()


@dataclass
class InputColumnMetaData:
    initial_name: str
    variable_type: InputColumnDataType
    unit: str
    priority: int


class InputDataFrameFormattingConfig:
    """
    Configuration class storing necessary attributes to format a
    DataFrame using the FormatDataForCRNSDataHub.
    """

    def __init__(
        self,
        path_to_config: str | Path | None = None,
        pressure_merge_method: MergeMethod = MergeMethod.PRIORITY,
        pressure_units: PressureUnits = PressureUnits.HECTOPASCALS,
        temperature_merge_method: MergeMethod = MergeMethod.PRIORITY,
        relative_humidity_merge_method: MergeMethod = MergeMethod.PRIORITY,
        neutron_count_units: NeutronCountUnits = NeutronCountUnits.ABSOLUTE_COUNT,
        date_time_columns: str | List[str] | None = None,
        date_time_format: str = "%Y/%m/%d %H:%M:%S",
        initial_time_zone: str = "utc",
        convert_time_zone_to: str = "utc",
        is_timestamp: bool = False,
        decimal: str = ".",
        start_date_of_data: str | pd.DatetimeIndex = None,
    ):
        """
        A class storing information supporting automated processing of
        raw input CRNS data files into a ready for neptoon dataframe
        (for use in FormatDataForCRNSDataHub)

        Parameters
        ----------
        path_to_config : Union[str, Path], optional
            path to the sensor configuration file by default None

        output_resolution : str, optional
            The desired time resolution of the dataframe to aggregate
            to. If None no time aggregation is done. Otherwise in format
            <number><unit>, by default None
        aggregate_method : Literal['fagg', 'bagg', 'nagg']
            Specifies which intervals to be aggregated for a certain
            timestamp. (preceding, succeeding or “surrounding”
            interval).
        aggregate_func : str
            Aggregation function. By default mean.
        aggregate_maxna_fraction : float, optional
            Maximum fraction of values in the aggregation period that
            can be NaN. If set to 0.3 only 30% of the values can be NaN
            by default 0.5
        align_timestamps: bool, optional
            Whether to align the time stamps to a regular time. E.g., If
            time_resolution is 1hour, 13:10, becomes 13:00, by default
            False.
        align_method: str, optional
            The alignment method to use by default "time", see
            https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html#saqc.SaQC.align
        pressure_merge_method : MergeMethod, optional
            Method used to merge multiple pressure columns, by default
            MergeMethod.PRIORITY
        pressure_units : PressureUnits, optional
            States the units of pressure for input data, will be
            converted to HECTOPASCALS
        temperature_merge_method : MergeMethod, optional
            Method used to merge multiple temperature columns,, by
            default MergeMethod.PRIORITY
        relative_humidity_merge_method : MergeMethod, optional
            Method used to merge multiple relative humidity columns,, by
            default MergeMethod.PRIORITY
        neutron_count_units : NeutronCountUnits, optional
            The units of neutron counts, by default
            NeutronCountUnits.ABSOLUTE_COUNT
        date_time_columns : List[str], optional
            Names of date time columns, if more than one expects DATE +
            TIME, by default None
        date_time_format : str, optional
            Format of the date time column, by default "%Y/%m/%d
            %H:%M:%S"
        initial_time_zone : str, optional
            Initial time zone, by default "utc"
        convert_time_zone_to : str, optional
            Desired time zone, by default "utc"
        is_timestamp : bool, optional
            Whether time stamp, by default False
        decimal : str, optional
            Decimal divider, by default "."
        start_date_of_data : str | pd.DateTime, optional
            The beginning date from which data should be processed. All
            data before this date is removed during parsing. Should
            always be in format: "%Y-%m-%d" e.g., 2024-04-22

        Notes
        -----
        For time_resolution, <number> is a positive integer and <unit>
        is one of:
            - For minutes: "min", "minute", "minutes"
            - For hours: "hour", "hours", "hr", "hrs"
            - For days: "day", "days"
        The parsing is case-insensitive.

        For *_merge_method parameters:
            - Mergemethod.MEAN: Average of all columns with the same
              data type.
            - Mergemethod.PRIORITY: Select one column from available
              columns based on predefined priority.
        """
        self.path_to_config = validate_and_convert_file_path(path_to_config)
        self.pressure_merge_method = pressure_merge_method
        self.pressure_units = pressure_units
        self.temperature_merge_method = temperature_merge_method
        self.relative_humidity_merge_method = relative_humidity_merge_method
        self.neutron_count_units = neutron_count_units
        self.date_time_columns = (
            str(ColumnInfo.Name.DATE_TIME)
            if date_time_columns is None
            else date_time_columns
        )
        self.date_time_format = date_time_format
        self.initial_time_zone = initial_time_zone
        self.convert_time_zone_to = convert_time_zone_to
        self.is_timestamp = is_timestamp
        self.decimal = decimal
        self.start_date_of_data = start_date_of_data
        self.column_data: List[InputColumnMetaData] = []

    def add_column_meta_data(
        self,
        initial_name: str,
        variable_type: InputColumnDataType,
        unit: str,
        priority: int,
    ):
        """
        Adds an InputColumnMetaData class to the column_data attribute.

        Parameters
        ----------
        initial_name : str
            The name of the column from the original raw data
        variable_type : InputColumnDataType
            Enum of the column data type: see InputColumnDataType
        unit : str
            The units of the column e.g., "hectopascals"
        priority : int
            The priority of the column - 1 being highest. Needed when
            multiple columns are present and the user wants to use the
            priority merge method (i.e., choose the best column for a
            data type).
        """

        self.column_data.append(
            (
                InputColumnMetaData(
                    initial_name=initial_name,
                    variable_type=variable_type,
                    unit=unit,
                    priority=priority,
                )
            )
        )

    def import_config(
        self,
        path_to_config: str = None,
    ):
        """
        Automatically assigns the internal attributes using a provided
        YAML file.

        Parameters
        ----------
        path_to_config : str, optional
            Location of the YAML file, if not supplied here it expects
            that the self.path_to_config attribute is already set, by default
            None

        Raises
        ------
        ValueError
            When no path is given but the method is called.
        """
        if path_to_config is None and self.path_to_config is None:
            message = "No path given for config file"
            core_logger.error(message)
            raise ValueError(message)
        else:
            path = (
                path_to_config
                if path_to_config is not None
                else self.path_to_config
            )

        internal_config = ConfigurationManager()
        internal_config.load_configuration(
            file_path=path,
        )

        self.config_info = internal_config.get_config("sensor")

    def build_from_config(self):
        """
        Assign attributes using the YAML information.
        """
        tmp = self.config_info
        self.neutron_count_units = (
            tmp.time_series_data.key_column_info.neutron_count_units
        )
        self.start_date_of_data = pd.to_datetime(
            tmp.sensor_info.install_date, format="%Y-%m-%d"
        )

        self.add_meteo_columns(
            meteo_columns=tmp.time_series_data.key_column_info.epithermal_neutron_columns,
            meteo_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit=self.neutron_count_units,
        )

        self.add_meteo_columns(
            meteo_columns=tmp.time_series_data.key_column_info.thermal_neutron_columns,
            meteo_type=InputColumnDataType.THERM_NEUTRON_COUNT,
            unit=self.neutron_count_units,
        )

        self.add_meteo_columns(
            meteo_columns=tmp.time_series_data.key_column_info.temperature_columns,
            meteo_type=InputColumnDataType.TEMPERATURE,
            unit=tmp.time_series_data.key_column_info.temperature_units,
        )
        self.add_meteo_columns(
            meteo_columns=tmp.time_series_data.key_column_info.pressure_columns,
            meteo_type=InputColumnDataType.PRESSURE,
            unit=tmp.time_series_data.key_column_info.pressure_units,
        )
        self.add_meteo_columns(
            meteo_columns=tmp.time_series_data.key_column_info.relative_humidity_columns,
            meteo_type=InputColumnDataType.RELATIVE_HUMIDITY,
            unit=tmp.time_series_data.key_column_info.relative_humidity_units,
        )
        self.assign_merge_methods(
            column_data_type=InputColumnDataType.PRESSURE,
            merge_method=tmp.time_series_data.key_column_info.pressure_merge_method,
        )
        self.assign_merge_methods(
            column_data_type=InputColumnDataType.TEMPERATURE,
            merge_method=tmp.time_series_data.key_column_info.temperature_merge_method,
        )
        self.assign_merge_methods(
            column_data_type=InputColumnDataType.RELATIVE_HUMIDITY,
            merge_method=tmp.time_series_data.key_column_info.relative_humidity_merge_method,
        )
        self.add_date_time_column_info(
            date_time_columns=tmp.time_series_data.key_column_info.date_time_columns,
            date_time_format=tmp.time_series_data.key_column_info.date_time_format,
            initial_time_zone=tmp.time_series_data.key_column_info.initial_time_zone,
            convert_time_zone_to=tmp.time_series_data.key_column_info.convert_time_zone_to,
        )

    def assign_merge_methods(
        self,
        column_data_type: InputColumnDataType,
        merge_method: str,
    ):
        """
        Assigns the merge method for each of the input columns.

        Parameters
        ----------
        column_data_type : InputColumnDataType
            The variable being assinged (as a InputColumnDataType)
        merge_method : str
            The selected merge methodq
        """
        if column_data_type == InputColumnDataType.PRESSURE:
            self.pressure_merge_method = merge_method
        elif column_data_type == InputColumnDataType.RELATIVE_HUMIDITY:
            self.relative_humidity_merge_method = merge_method
        elif column_data_type == InputColumnDataType.TEMPERATURE:
            self.temperature_merge_method = merge_method

    def add_meteo_columns(
        self,
        meteo_columns: List,
        meteo_type: InputColumnDataType,
        unit: str,
    ):
        """
        Adds column meta data to the class instance. Intended for use
        when importing attributes with the YAML file.

        There can be more than one column recording the same variable.
        These are recorded in the YAML in priority order e.g.,:

            pressure_columns:
                - P4_mb # first priorty goes first
                - P3_mb
                - P1_mb

        This method will go through the list in priority order, create a
        InputColumnMetaData class for each column, assign the
        appropriate values, and add it to self.column_data using the
        method self.add_column_meta_data.

        Parameters
        ----------
        meteo_columns : List
            A list of column names
        meteo_type : InputColumnDataType
            The type of column being attributed
        unit : str
            The units associated with the column
        """
        if meteo_columns is None:
            return
        available_cols = [name for name in meteo_columns]
        priority = 1
        for col in available_cols:
            self.add_column_meta_data(
                initial_name=col,
                variable_type=meteo_type,
                unit=unit,
                priority=priority,
            )
            priority += 1

    def add_date_time_column_info(
        self,
        date_time_columns: List,
        date_time_format: str,
        initial_time_zone: str,
        convert_time_zone_to: str = "UTC",
    ):
        """
        Adds datetime column information. Intended for use when
        importing attributes with the YAML file.

        Parameters
        ----------
        date_time_columns : List
            Names of date time columns
        date_time_format : str
            The expected format of the date time values.
        initial_time_zone : str
            The intial time zone of the data
        convert_time_zone_to : str
            The desired time zone, by default "UTC"
        """
        self.date_time_columns = [col for col in date_time_columns]
        self.date_time_format = date_time_format.replace('"', "")
        self.initial_time_zone = initial_time_zone
        self.convert_time_zone_to = convert_time_zone_to


class FormatDataForCRNSDataHub:
    """
    Formats a DataFrame into the required format to work in neptoon.

    Key features:
        - Combines multiple datetime columns (e.g., DATE + TIME) into a
          single date_time column
        - Converts time zone (default UTC)
        - Ensures date time index
        - Ensures columns are numeric
        - Organises columns when multiple are present

    Attributes
    ----------

    data_frame: pd.DataFrame
        The time series dataframe
    config: InputDataFrameFormattingConfig
        Config object with information about the dataframe, which
        supports formatting

    """

    def __init__(
        self,
        data_frame: pd.DataFrame,
        config: InputDataFrameFormattingConfig,
    ):
        """
        Attributes of class

        Parameters
        ----------
        data_frame : pd.DataFrame
            The un-formatted dataframe
        config : InputDataFrameConfig
            Config Object which sets the options for formatting, by
            default None
        """
        self._data_frame = data_frame
        self._config = config
        self._timestep_seconds = None
        # self.conversion_factor_to_cph = None

    @property
    def data_frame(self):
        return self._data_frame

    @property
    def config(self):
        return self._config

    @data_frame.setter
    def data_frame(
        self,
        df: pd.DataFrame,
    ):
        self._data_frame = df

    def extract_date_time_column(
        self,
    ) -> pd.Series:
        """
        Create a Datetime column, merge columns if necessary (e.g., when
        columns are split into date and time)

        Returns:
            pd.Series: the Datetime column.
        """
        if isinstance(self.config.date_time_columns, str):
            dt_series = self.data_frame[self.config.date_time_columns]
        elif isinstance(self.config.date_time_columns, list):
            # Select Columns
            for col_name in self.config.date_time_columns:
                if isinstance(col_name, str):
                    dt_series = pd.concat(
                        [
                            self.data_frame[col].astype(str)
                            for col in self.config.date_time_columns
                        ],
                        axis=1,
                    ).apply(lambda x: " ".join(x.values), axis=1)
                else:
                    message = (
                        "date_time_columns must contain only string "
                        "type column names"
                    )
                    core_logger.error(message)
                    raise ValueError(message)
        else:
            message = "date_time_columns must be either a string or a list of strings"
            core_logger.error(message)
            raise ValueError(message)

        dt_series = pd.to_datetime(
            dt_series,
            errors="coerce",
            unit="s" if self.config.is_timestamp else None,
            format=self.config.date_time_format,
        )

        return dt_series

    def convert_time_zone(self, date_time_series):
        """
        Convert the timezone of a date time time series. Uses the
        attributes initial_time_zone (the actual time zone the data is
        currently in) and convert_time_zone_to which is the desired time
        zone. This is default set the UTC time.

        Parameters
        ----------
        date_time_series : pd.Series
            The date_time_series that is converted

        Returns
        -------
        pd.Series
            The converted date_time series in the correct time zone
        """
        if date_time_series[0].tzinfo is None:
            date_time_series = date_time_series.dt.tz_localize(
                self.config.initial_time_zone
            )
        if self.config.initial_time_zone != self.config.convert_time_zone_to:
            date_time_series = date_time_series.dt.tz_convert(
                self.config.convert_time_zone_to
            )
        return date_time_series

    def date_time_as_index(
        self,
    ) -> pd.DataFrame:
        """
        Sets a date_time column as the index of the contained DataFrame

        Returns:
            pd.DataFrame: data with a DatetimeIndex
        """

        date_time_column = self.extract_date_time_column()
        # if all values are NaT, raise error
        if date_time_column.isnull().all():
            message = "Could not parse date column(s). Please check date_time_format and date_time_columns."
            core_logger.error(message)
            raise ValueError(message)
        date_time_column = self.convert_time_zone(date_time_column)
        self.data_frame.index = date_time_column
        self.data_frame.sort_index(inplace=True)
        self.data_frame.drop(
            self.config.date_time_columns, axis=1, inplace=True
        )

    def data_frame_to_numeric(
        self,
    ):
        """
        Convert DataFrame columns to numeric values.
        """
        # Cases when decimal is not '.', replace them by '.'
        decimal = self.config.decimal
        decimal = decimal.strip()
        if decimal != ".":
            self.data_frame = self.data_frame.apply(
                lambda x: x.str.replace(decimal, ".")
            )

        # Convert all the regular columns to numeric and drop any failures
        self.data_frame = self.data_frame.apply(pd.to_numeric, errors="coerce")

    def get_conversion_factor_to_cph(
        self,
        timestep_seconds: int,
    ):
        """
        Figures out the factor needed to multiply a count rate by to
        convert it to counts per hour. Uses the time_resolution
        attribute for this calculation.

        Returns
        -------
        float
            The factor to convert to counts per hour
        """

        hours = timestep_seconds / 3600
        return 1 / hours

    def standardise_units_of_pressure(self):
        """
        Standardises units of pressure to hectopascals
        """
        pressure_cols = [
            col
            for col in self.config.column_data
            if col.variable_type is InputColumnDataType.PRESSURE
        ]

        for pressure_col in pressure_cols:
            if pressure_col.unit == PressureUnits.PASCALS:
                self.data_frame[pressure_col.initial_name] = (
                    self.data_frame[pressure_col.initial_name] / 100
                )
                pressure_col.unit = PressureUnits.HECTOPASCALS
            elif pressure_col.unit == PressureUnits.KILOPASCALS:
                self.data_frame[pressure_col.initial_name] = (
                    self.data_frame[pressure_col.initial_name] * 10
                )
                pressure_col.unit = PressureUnits.HECTOPASCALS

    def merge_multiple_meteo_columns(
        self,
        column_data_type: Literal[
            InputColumnDataType.PRESSURE,
            InputColumnDataType.RELATIVE_HUMIDITY,
            InputColumnDataType.TEMPERATURE,
        ],
    ):
        """
        Merges columns when multiple are available. Many CRNS have
        multiple sensors available in the input dataset (e.g., 2 or more
        pressure sensors at the site). We need only one value for each
        of these variables. This method uses the settings in the
        DataFrameConfig class to produce a single sensor value for the
        selected sensor.

        Current Options (set in the Config file):
            mean - create an average of all the pressure sensors
            priority - use one sensor selected as priority

        Future Options:
            priority_filled - use one sensor as priorty and fill values
            from alternative seno

        Parameters
        ----------
        column_data_type : InputColumnDataType
            One of the possible InputColumnDataTypes that can be used
            here.

        Raises
        ------
        ValueError
            If an incompatible InputColumnDataType is given
        """

        if column_data_type == InputColumnDataType.PRESSURE:
            merge_method = self.config.pressure_merge_method
            created_col_name = str(ColumnInfo.Name.AIR_PRESSURE)
        elif column_data_type == InputColumnDataType.TEMPERATURE:
            merge_method = self.config.temperature_merge_method
            created_col_name = str(ColumnInfo.Name.AIR_TEMPERATURE)
        elif column_data_type == InputColumnDataType.RELATIVE_HUMIDITY:
            merge_method = self.config.relative_humidity_merge_method
            created_col_name = str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY)
        else:
            message = (
                f"{column_data_type} is incompatible with this method to merge"
            )
            core_logger.error(message)
            raise ValueError(message)
            return

        if merge_method == "priority":
            try:
                priority_col = next(
                    col
                    for col in self.config.column_data
                    if col.variable_type is column_data_type
                    and col.priority == 1
                )

                additional_priority_cols = sum(
                    1
                    for col in self.config.column_data
                    if col.variable_type is column_data_type
                    and col.priority == 1
                )
                if additional_priority_cols > 1:
                    message = (
                        f"More than one {column_data_type} column given top priority. "
                        f"Using column '{priority_col.initial_name}'. For future reference "
                        "it is better to give only one column top priority when "
                        "using 'priority' merge method"
                    )
                    core_logger.info(message)

                self.data_frame.rename(
                    columns={priority_col.initial_name: created_col_name},
                    inplace=True,
                )
            except StopIteration:
                raise ValueError(
                    f"No column found with priority 1 for type {column_data_type}"
                )

        elif merge_method == "mean":
            available_cols = [
                col
                for col in self.config.column_data
                if col.variable_type is column_data_type
            ]
            pressure_col_names = [col.initial_name for col in available_cols]
            self.data_frame[created_col_name] = self.data_frame[
                pressure_col_names
            ].mean(axis=1)

    def prepare_key_columns(self):
        """
        Prepares the key columns if all the information has been
        supplied.
        """
        self.standardise_units_of_pressure()
        self.merge_multiple_meteo_columns(
            column_data_type=InputColumnDataType.PRESSURE
        )

        self.merge_multiple_meteo_columns(
            column_data_type=InputColumnDataType.TEMPERATURE
        )
        self.merge_multiple_meteo_columns(
            column_data_type=InputColumnDataType.RELATIVE_HUMIDITY
        )
        self.prepare_neutron_count_columns(
            neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
        )
        try:
            self.prepare_neutron_count_columns(
                neutron_column_type=InputColumnDataType.THERM_NEUTRON_COUNT
            )
        except Exception as e:
            message = f"Could not process thermal_neutron_counts. {e}"
            core_logger.info(message)

    def _calc_timestep_diff(self, data_frame: pd.DataFrame):
        """
        Infer timestep in seconds

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame

        Returns
        -------
        data_frame
            DataFrame with timestep column
        """
        # infer from timestamp difference
        data_frame[str(ColumnInfo.Name.TIME_STEP_SECONDS)] = (
            data_frame.index.to_series().diff().dt.total_seconds()
        )
        return data_frame

    def _merge_multiple_neutron_cols(
        self,
        neutron_column_type: Literal[
            InputColumnDataType.EPI_NEUTRON_COUNT,
            InputColumnDataType.THERM_NEUTRON_COUNT,
        ],
        raw_column_name: str,
    ):
        """
        Merges multiple neutron columns (either epithermal or thermal)
        into a single column by summing the values

        Parameters
        ----------
        neutron_column_type : Literal[
        InputColumnDataType.EPI_NEUTRON_COUNT,
        InputColumnDataType.THERM_NEUTRON_COUNT, ]
            Neutron Column type as Enum
        raw_column_name : str
            The name of the column where raw data will be stored.
        """
        neutron_cols = [
            col
            for col in self.config.column_data
            if col.variable_type is neutron_column_type
        ]

        if len(neutron_cols) > 1:
            epi_col_names = [name.initial_name for name in neutron_cols]

            self.data_frame[raw_column_name] = self.data_frame[
                epi_col_names
            ].sum(axis=1)
        else:
            neutron_col_name = neutron_cols[0].initial_name
            self.data_frame.rename(
                columns={neutron_col_name: raw_column_name},
                inplace=True,
            )

    def _convert_neutron_units_to_cph(
        self,
        neutron_column_type: Literal[
            InputColumnDataType.EPI_NEUTRON_COUNT,
            InputColumnDataType.THERM_NEUTRON_COUNT,
        ],
        raw_column_name: str,
        final_column_name: str,
    ):
        epi_neutron_unit = next(
            col.unit
            for col in self.config.column_data
            if col.variable_type is neutron_column_type
        )

        if epi_neutron_unit == "counts_per_hour":
            self.data_frame[final_column_name] = self.data_frame[
                raw_column_name
            ]
            self.data_frame["hours_fraction"] = (
                self.data_frame[str(ColumnInfo.Name.TIME_STEP_SECONDS)] / 3600
            )
            self.data_frame[raw_column_name] = (
                self.data_frame[raw_column_name]
                * self.data_frame["hours_fraction"]
            )
            self.data_frame.drop("hours_fraction", axis=1, inplace=True)

        elif epi_neutron_unit == "absolute_count":
            self.data_frame["factor_to_cph"] = self.data_frame.apply(
                lambda row: self.get_conversion_factor_to_cph(
                    row[str(ColumnInfo.Name.TIME_STEP_SECONDS)]
                ),
                axis=1,
            )

            self.data_frame[final_column_name] = (
                self.data_frame[raw_column_name]
                * self.data_frame["factor_to_cph"]
            )

        elif epi_neutron_unit == "counts_per_second":
            self.data_frame[final_column_name] = (
                self.data_frame[raw_column_name] * 3600
            )
            self.data_frame[raw_column_name] = (
                self.data_frame[raw_column_name]
                * self.data_frame[str(ColumnInfo.Name.TIME_STEP_SECONDS)]
            )

    def prepare_neutron_count_columns(
        self,
        neutron_column_type: Literal[
            InputColumnDataType.EPI_NEUTRON_COUNT,
            InputColumnDataType.THERM_NEUTRON_COUNT,
        ],
    ):
        """
        Prepares the neutron columns for usage in neptoon. Performs
        several steps:

            - Finds the columns labeled with neutron_column_type
            - If more than one it will sum them into a new column
            - Check the units and convert to counts per hour.


        Parameters
        ----------
        neutron_column_type :
                    Literal[
                        InputColumnDataType.EPI_NEUTRON_COUNT,
                        InputColumnDataType.THERM_NEUTRON_COUNT,
                            ]
            The type of neutron data being processed
        """
        self.data_frame = self._calc_timestep_diff(data_frame=self.data_frame)

        if neutron_column_type == InputColumnDataType.EPI_NEUTRON_COUNT:
            raw_column_name = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)
            final_column_name = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)
        elif neutron_column_type == InputColumnDataType.THERM_NEUTRON_COUNT:
            raw_column_name = str(ColumnInfo.Name.THERM_NEUTRON_COUNT_RAW)
            final_column_name = str(ColumnInfo.Name.THERM_NEUTRON_COUNT_CPH)

        self._merge_multiple_neutron_cols(
            neutron_column_type=neutron_column_type,
            raw_column_name=raw_column_name,
        )

        self._convert_neutron_units_to_cph(
            neutron_column_type=neutron_column_type,
            raw_column_name=raw_column_name,
            final_column_name=final_column_name,
        )

    def clean_raw_dataframe(self):
        """
        Cleans raw DataFrame by removing NaT values and duplicated rows.
        """
        original_size = len(self.data_frame)

        # Remove NaT index values
        self.data_frame = self.data_frame[self.data_frame.index.notna()]
        nat_removed = original_size - len(self.data_frame)
        if nat_removed > 0:
            core_logger.info(f"Removed {nat_removed} rows with NaT index")

        # Remove duplicates
        if self.data_frame.index.duplicated().any():
            duplicate_count = self.data_frame.index.duplicated().sum()
            self.data_frame = self.data_frame[
                ~self.data_frame.index.duplicated(keep="first")
            ]
            core_logger.info(f"Removed {duplicate_count} duplicate rows")

    def calc_neutron_uncertainty(self):
        """
        Creates a column with the statistical uncertainty of the neutron
        column and converts this value to counts per hour.
        """
        self.data_frame["factor_to_cph"] = self.data_frame.apply(
            lambda row: self.get_conversion_factor_to_cph(
                row[str(ColumnInfo.Name.TIME_STEP_SECONDS)]
            ),
            axis=1,
        )

        self.data_frame[
            str(ColumnInfo.Name.RAW_EPI_NEUTRON_COUNT_UNCERTAINTY)
        ] = np.sqrt(
            self.data_frame[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)]
        )
        self.data_frame[
            str(ColumnInfo.Name.RAW_EPI_NEUTRON_COUNT_UNCERTAINTY)
        ] = (
            self.data_frame[
                str(ColumnInfo.Name.RAW_EPI_NEUTRON_COUNT_UNCERTAINTY)
            ]
            * self.data_frame["factor_to_cph"]
        )

    def snip_data_frame(self):
        """
        Removes data from before the defined install date.
        """
        if self.config.start_date_of_data is not None:
            start_date = pd.to_datetime(
                self.config.start_date_of_data, format="%Y-%m-%d"
            ).tz_localize("UTC")
            self.data_frame = self.data_frame[
                ~(self.data_frame.index < start_date)
            ]

    def format_data_and_return_data_frame(
        self,
    ):
        """
        Completes the whole process of formatting the dataframe. Expects
        the settings to be fully implemented.

        Returns
        -------
        pd.DataFrame
            DataFrame
        """
        self.date_time_as_index()
        self._timestep_seconds = find_temporal_resolution_seconds(
            self.data_frame
        )
        self.clean_raw_dataframe()
        if self.data_frame.empty:
            message = f"No data found after parsing from {self._config.config_info.raw_data_parse_options.data_location}. Please check config file and data source. "
            core_logger.error(message)
            raise ValueError(message)

        self.data_frame_to_numeric()
        self.conversion_factor_to_cph = self.get_conversion_factor_to_cph(
            self._timestep_seconds
        )
        self.prepare_key_columns()
        self.calc_neutron_uncertainty()
        self.snip_data_frame()
        return self.data_frame


class CollectAndParseRawData:
    """
    Central class which allows us to do the entire ingest and
    formatting routine. Designed to work with a YAML file.
    """

    def __init__(
        self,
        path_to_config: Union[str, Path],
        file_collection_config: FileCollectionConfig = None,
        input_formatter_config: InputDataFrameFormattingConfig = None,
    ):
        self._path_to_config = validate_and_convert_file_path(path_to_config)
        self.file_collection_config = file_collection_config
        self.input_formatter_config = input_formatter_config

    @property
    def path_to_config(self):
        return self._path_to_config

    @path_to_config.setter
    def path_to_config(self, new_path):
        return validate_and_convert_file_path(new_path)

    def create_data_frame(self):
        """
        Creates the data frame by parsing raw data files into a
        DataFrame. It expects to use a YAML file.

        Returns
        -------
        _type_
            _description_
        """
        self.file_collection_config = FileCollectionConfig(
            path_to_config=self.path_to_config
        )
        self.file_collection_config.build_from_config()
        file_manager = ManageFileCollection(config=self.file_collection_config)
        file_manager.create_file_list()
        file_parser = ParseFilesIntoDataFrame(
            file_manager=file_manager, config=self.file_collection_config
        )
        parsed_data = file_parser.make_dataframe()

        self.input_formatter_config = InputDataFrameFormattingConfig(
            path_to_config=self.path_to_config
        )
        self.input_formatter_config.import_config()
        self.input_formatter_config.build_from_config()
        data_formatter = FormatDataForCRNSDataHub(
            data_frame=parsed_data,
            config=self.input_formatter_config,
        )
        df = data_formatter.format_data_and_return_data_frame()
        return df
