import pandas as pd
import tarfile
import re
from datetime import timedelta
from dataclasses import dataclass
from enum import Enum, auto
import zipfile
import io
from saqc import SaQC
from pathlib import Path
from typing import Union, Literal, List, Optional

from neptoon.quality_control.data_audit import log_key_step
from neptoon.logging import get_logger
from neptoon.utils.general_utils import validate_and_convert_file_path
from neptoon.columns.column_information import ColumnInfo
from neptoon.config.configuration_input import (
    ConfigurationManager,
)

core_logger = get_logger()


# ######
# def validate_and_convert_file_path(
#     file_path: Union[str, Path],
#     base: Union[str, Path] = "",
# ) -> Path:
#     """
#     Used when initialising the object. If a string is given as a
#     data_location, it is converted to a pathlib.Path object. If a
#     pathlib.Path object is given this is returned. Other types will
#     cause an error.

#     Parameters
#     ----------
#     data_location : Union[str, Path]
#         The data_location attribute from initialisation.

#     Returns
#     -------
#     pathlib.Path
#         The data_location as a pathlib.Path object.

#     Raises
#     ------
#     ValueError
#         Error if string or pathlib.Path given.
#     """

# if file_path is None:
#     return None
# if isinstance(file_path, str):
#     new_file_path = Path(file_path)
#     if new_file_path.is_absolute():
#         return new_file_path
#     else:
#         return base / Path(file_path).resolve()
# elif isinstance(file_path, Path):
#     if file_path.is_absolute():
#         return file_path
#     else:
#         return base / file_path
# else:
#     message = (
#         "data_location must be of type str or pathlib.Path. \n"
#         f"{type(file_path).__name__} provided, "
#         "please change this."
#     )
#     core_logger.error(message)
#     raise ValueError(message)


class FileCollectionConfig:
    """
    Configuration class for file collection and parsing settings.

    This class holds all the necessary parameters for locating, reading,
    and parsing data files, providing a centralized configuration for
    the data ingestion process.
    """

    def __init__(
        self,
        path_to_yaml: Union[str, Path] = None,
        data_location: Union[str, Path] = None,
        column_names: list = None,
        prefix="",
        suffix="",
        encoding="cp850",
        skip_lines: int = 0,
        separator: str = ",",
        decimal: str = ".",
        skip_initial_space: bool = True,
        parser_kw: dict = dict(
            strip_left=True,
            digit_first=True,
        ),
        starts_with: any = "",
        multi_header: bool = False,
        strip_names: bool = True,
        remove_prefix: str = "//",
    ):
        """
        Initial parameters for data collection and merging

        Parameters
        ----------
        path_to_yaml : Union[str, Path]
            The location of the yaml file. Can be either a string or
            Path object
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
        self._path_to_yaml = validate_and_convert_file_path(
            file_path=path_to_yaml
        )
        self._data_location = validate_and_convert_file_path(
            file_path=data_location,
            base=(
                self.path_to_yaml.parent
                if self.path_to_yaml is not None
                else ""
            ),
        )
        self._data_source = None
        self.column_names = column_names
        self.prefix = prefix
        self.suffix = suffix
        self.encoding = encoding
        self.skip_lines = skip_lines
        self.parser_kw = parser_kw
        self._separator = separator
        self._decimal = decimal
        self.skip_initial_space = skip_initial_space
        self.starts_with = starts_with
        self.multi_header = multi_header
        self.strip_names = strip_names
        self._remove_prefix = remove_prefix

        self._determine_source_type()

    @property
    def path_to_yaml(self):
        return self._path_to_yaml

    @path_to_yaml.setter
    def path_to_yaml(self, new_path):
        self._path_to_yaml = validate_and_convert_file_path(new_path)

    @property
    def data_location(self):
        return self._data_location

    @data_location.setter
    def data_location(self, new_location):
        self._data_location = validate_and_convert_file_path(
            new_location, base=self._path_to_yaml.parent
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
        elif tarfile.is_tarfile(self._data_location):
            self._data_source = "tarfile"
            core_logger.info("Extracting data from a tarfile")
        elif zipfile.is_zipfile(self._data_location):
            self._data_source = "zipfile"
            core_logger.info("Extracting data from a zipfile")
        else:
            self._data_source = None
            core_logger.warning("Cannot determine data source type")

    def _return_list_of_files_from_folder(self) -> list:
        """
        Returns the list of files from a given folder.

        Returns
        -------
        list
            list of files contained in the folder
        """
        files = []
        if self._data_location.is_dir():
            try:
                item_list = self._data_location.glob("**/*")
                files = [x.name for x in item_list if x.is_file()]
            except FileNotFoundError as fnf_error:
                message = (
                    f"! Folder not found: {self._data_location}. "
                    f"Error: {fnf_error}"
                )
                core_logger.error(message)
                raise
            except Exception as err:
                message = (
                    f"! Error accessing folder {self._data_location}. "
                    f"Error: {err}"
                )
                core_logger.error(message)
                raise
        return files

    def build_from_yaml(
        self,
        path_to_yaml: Optional[Union[Path, str]] = None,
    ):
        """
        Imports the attributes for the instance of FileCollectionConfig
        from a pre-configured YAML file

        Parameters
        ----------
        path_to_yaml : Union[Path, str], optional
            Path to the pre-configured YAML file, by default None

        Raises
        ------
        ValueError
            If no suitable path given
        """
        if path_to_yaml is None and self._path_to_yaml is None:
            message = "No path given for yaml file"
            core_logger.error(message)
            raise ValueError(message)
        else:
            path = (
                path_to_yaml
                if path_to_yaml is not None
                else self._path_to_yaml
            )
            path = validate_and_convert_file_path(path)

        internal_config = ConfigurationManager()
        internal_config.load_and_validate_configuration(
            name="input_data",
            file_path=path,
        )
        yaml_information = internal_config.get_configuration("input_data")

        self.data_location = (
            yaml_information.raw_data_parse_options.data_location
        )
        self.column_names = (
            yaml_information.raw_data_parse_options.column_names
        )
        self.prefix = yaml_information.raw_data_parse_options.prefix
        self.suffix = yaml_information.raw_data_parse_options.suffix
        self.encoding = yaml_information.raw_data_parse_options.encoding
        self.skip_lines = yaml_information.raw_data_parse_options.skip_lines
        self.parser_kw = (
            yaml_information.raw_data_parse_options.parser_kw.to_dict()
        )
        self.separator = yaml_information.raw_data_parse_options.separator
        self.decimal = yaml_information.raw_data_parse_options.decimal
        self.skip_initial_space = (
            yaml_information.raw_data_parse_options.skip_initial_space
        )
        self.starts_with = yaml_information.raw_data_parse_options.starts_with
        self.multi_header = (
            yaml_information.raw_data_parse_options.multi_header
        )
        self.strip_names = yaml_information.raw_data_parse_options.strip_names
        self.remove_prefix = (
            yaml_information.raw_data_parse_options.remove_prefix
        )


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

    def _return_list_of_files_from_folder(self) -> list:
        """
        Returns the list of files from a given folder.

        Returns
        -------
        list
            list of files contained in the folder
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

        return files

    def _return_list_of_files_from_zip(self) -> list:
        """
        Returns a list of files from a zip.

        Returns
        -------
        list
            list of files contained in the zip
        """
        files = []
        try:
            with zipfile.ZipFile(self.config.data_location, "r") as archive:
                files = archive.namelist()

        except FileNotFoundError as fnf_error:
            message = (
                f"! Archive file not found: {self.config.data_location}."
                f"Error: {fnf_error}"
            )

            raise
        except Exception as err:
            message = (
                f"! Error accessing archive {self.config.data_location}. "
                f"Error: {err}"
            )
            core_logger.error(message)
            raise

        return files

    def _return_list_of_files_from_tar(self) -> list:
        """
        Returns a list of files from a tar.

        Returns
        -------
        list
            list of files contained in the tar
        """
        files = []
        try:
            with tarfile.TarFile(self.config.data_location, "r") as archive:
                files = archive.getnames()

        except FileNotFoundError as fnf_error:
            message = (
                f"! Archive file not found: {self.config.data_location}."
                f"Error: {fnf_error}"
            )

            raise
        except Exception as err:
            message = (
                f"! Error accessing archive {self.config.data_location}. "
                f"Error: {err}"
            )
            core_logger.error(message)
            raise

        return files

    def get_list_of_files(self):
        """
        Lists the files found at the data_location and assigns these to
        the file attribute.
        """
        if self.config.data_source == "folder":
            self.files = self._return_list_of_files_from_folder()
        elif self.config.data_source == "zipfile":
            self.files = self._return_list_of_files_from_zip()
        elif self.config.data_source == "tarfile":
            self.files = self._return_list_of_files_from_tar()
        else:
            message = (
                "Data source appears to not be folder, zip or tar file.\n"
                "Cannot collect file names."
            )
            core_logger.error(message)
            raise ValueError(message)

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
        self.files = files_filtered


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
            if self.config.data_source == "folder":
                return open(
                    self.config.data_location / filename,
                    encoding=encoding,
                )
            elif self.config.data_source == "tarfile":
                archive = tarfile.open(self.config.data_location, "r")
                return archive.extractfile(filename)
            elif self.config.data_source == "zipfile":
                archive = zipfile.ZipFile(self.config.data_location, "r")
                return archive.open(filename)
            else:
                message = (
                    "Unsupported data type at source folder. It must be "
                    "a folder, zipfile, or tarfile."
                )
                core_logger.error(message)
                raise ValueError(message)
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
        if isinstance(line, bytes) and self.config.encoding != "":
            line = line.decode(self.config.encoding, errors="ignore")

        if self.config.parser_kw["strip_left"]:
            line = line.lstrip()

        # If the line starts with a number, it likely is actual data
        if self.config.parser_kw["digit_first"] and not line[:1].isdigit():
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

    Attributes
    ----------
    yaml_path : str | Path
        The path to the YAML file storing attribute information
    time_resolution : str
        Time resolution in format "<number> <unit>".
    pressure_merge_method : {'mean', 'priority'}, optional
        Method for merging pressure data, by default 'priority'.
    temperature_merge_method : {'mean', 'priority'}, optional
        Method for merging temperature data, by default 'priority'.
    relative_humidity_merge_method : {'mean', 'priority'}, optional
        Method for merging relative humidity data, by default
        'priority'.
    neutron_count_units :

    Methods
    -------
    - parse_resolution
    - get_conversion_factor
    - add_column_meta_data
    - build_from_yaml
    - assign_merge_methods
    - add_meteo_columns
    - add_date_time_column_info
    - add_neutron_columns
    """

    def __init__(
        self,
        path_to_yaml: Optional[Union[str, Path]] = None,
        time_resolution: str = "1hour",
        pressure_merge_method: MergeMethod = MergeMethod.PRIORITY,
        temperature_merge_method: MergeMethod = MergeMethod.PRIORITY,
        relative_humidity_merge_method: MergeMethod = MergeMethod.PRIORITY,
        neutron_count_units: NeutronCountUnits = NeutronCountUnits.ABSOLUTE_COUNT,
        date_time_columns: Optional[Union[str, List[str]]] = None,
        date_time_format: str = "%Y/%m/%d %H:%M:%S",
        initial_time_zone: str = "utc",
        convert_time_zone_to: str = "utc",
        is_timestamp: bool = False,
        decimal: str = ".",
    ):
        """
        A class storing information supporting automated processing of
        raw input CRNS data files into a ready for neptoon dataframe
        (for use in FormatDataForCRNSDataHub)

        Parameters
        ----------
        path_to_yaml : Union[str, Path], optional
            path for a YAML file to automate the build, by default None
        time_resolution : str, optional
            Time resolution in format "<number><unit>, by default
            "1hour"
        pressure_merge_method : MergeMethod, optional
            Method used to merge multiple pressure columns, by default
            MergeMethod.PRIORITY
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
        self.path_to_yaml = validate_and_convert_file_path(path_to_yaml)
        self._time_resolution = self.parse_resolution(time_resolution)
        self._conversion_factor_to_counts_per_hour = (
            self.get_conversion_factor()
        )
        self.pressure_merge_method = pressure_merge_method
        self.temperature_merge_method = temperature_merge_method
        self.relative_humidity_merge_method = relative_humidity_merge_method
        self.neutron_count_units = neutron_count_units
        self.date_time_columns = date_time_columns
        self.date_time_format = date_time_format
        self.initial_time_zone = initial_time_zone
        self.convert_time_zone_to = convert_time_zone_to
        self.is_timestamp = is_timestamp
        self.decimal = decimal
        self.column_data: List[InputColumnMetaData] = []

    @property
    def time_resolution(self):
        return self._time_resolution

    @property
    def conversion_factor_to_counts_per_hour(self):
        return self._conversion_factor_to_counts_per_hour

    @conversion_factor_to_counts_per_hour.setter
    def conversion_factor_to_counts_per_hour(self, value):
        self._conversion_factor_to_counts_per_hour = value

    @time_resolution.setter
    def time_resolution(self, value):
        """
        When setting the time_resoltion this method ensures the
        conversion factor is updated.

        Parameters
        ----------
        value : str
            Time resolution
        """
        self._time_resolution = self.parse_resolution(value)
        self._conversion_factor_to_counts_per_hour = (
            self.get_conversion_factor()
        )

    def parse_resolution(
        self,
        resolution_str: str,
    ):
        """
        Parse a string representation of a time resolution and convert
        it to a timedelta object.

        This method takes a string describing a time resolution (e.g.,
        "30 minutes", "2 hours", "1 day") and converts it into a Python
        timedelta object. It supports minutes, hours, and days as units.

        Parameters
        ----------
        resolution_str : str
            A string representing the time resolution. The format should
            be "<number> <unit>", where <number> is a positive integer
            and <unit> is one of the following: - For minutes: "min",
            "minute", "minutes" - For hours: "hour", "hours", "hr",
            "hrs" - For days: "day", "days" The parsing is
            case-insensitive.

        Returns
        -------
        datetime.timedelta
            A timedelta object representing the parsed time resolution.

        Raises
        ------
        ValueError
            If the resolution string format is invalid or cannot be
            parsed.
        ValueError
            If an unsupported time unit is provided.
        """

        pattern = re.compile(r"(\d+)\s*([a-zA-Z]+)")
        match = pattern.match(resolution_str.strip())

        if not match:
            raise ValueError(f"Invalid resolution format: {resolution_str}")

        value, unit = match.groups()
        value = int(value)

        if unit.lower() in ["min", "mins", "minute", "minutes"]:
            return timedelta(minutes=value)
        elif unit.lower() in ["hour", "hours", "hr", "hrs"]:
            return timedelta(hours=value)
        elif unit.lower() in ["day", "days"]:
            return timedelta(days=value)
        else:
            message = f"Unsupported time unit: {unit}"
            core_logger.error(message)
            raise ValueError(message)

    def get_conversion_factor(self):
        """
        Figures out the factor needed to multiply a count rate by to
        convert it to counts per hour. Uses the time_resolution
        attribute for this calculation.

        Returns
        -------
        float
            The factor to convert to counts per hour
        """

        hours = self.time_resolution.total_seconds() / 3600
        return 1 / hours

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

    def import_yaml(
        self,
        path_to_yaml: str = None,
    ):
        """
        Automatically assigns the internal attributes using a provided
        YAML file.

        Parameters
        ----------
        path_to_yaml : str, optional
            Location of the YAML file, if not supplied here it expects
            that the self.yaml_path attribute is already set, by default
            None

        Raises
        ------
        ValueError
            When no path is given but the method is called.
        """
        if path_to_yaml is None and self.path_to_yaml is None:
            message = "No path given for yaml file"
            core_logger.error(message)
            raise ValueError(message)
        else:
            path = (
                path_to_yaml if path_to_yaml is not None else self.path_to_yaml
            )

        internal_config = ConfigurationManager()
        internal_config.load_and_validate_configuration(
            name="station",
            file_path=path,
        )

        self.yaml_information = internal_config.get_configuration("station")

    def build_from_yaml(self):
        """
        Assign attributes using the YAML information.
        """
        tmp = self.yaml_information

        self.time_resolution = tmp.time_series_data.time_step_resolution

        self.neutron_count_units = (
            tmp.time_series_data.key_column_info.neutron_count_units
        )

        self.add_meteo_columns(
            meteo_columns=tmp.time_series_data.key_column_info.epithermal_neutron_counts_columns,
            meteo_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit=self.neutron_count_units,
        )

        self.add_meteo_columns(
            meteo_columns=tmp.time_series_data.key_column_info.thermal_neutrons,
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
    Formats a DataFrame into the requred format for work in neptoon.

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

    Methods
    -------

    extract_date_time_column
    convert_time_zone
    align_time_stamps
    date_time_as_index
    data_frame_to_numeric
    aggregate_data_frame TODO
    merge_multiple_meteo_columns
    prepare_key_columns
    prepare_neutron_count_columns
    format_data_and_return_data_frame
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
            temp_columns = []
            for col_name in self.config.date_time_columns:
                if isinstance(col_name, str):
                    temp_columns.append(self.data_frame[col_name])
                else:
                    message = (
                        "date_time_columns must contain only string "
                        "type column names"
                    )
                    core_logger.error(message)
                    raise ValueError(message)

            # Join columns together separated with a space
            # dt_series = self.data_frame[temp_columns].apply(
            #     lambda x: "{} {}".format(x[0], x[1]), axis=1
            # )
            if len(temp_columns) == 1:
                dt_series = temp_columns[0]
            else:
                dt_series = pd.concat(temp_columns, axis=1).apply(
                    " ".join, axis=1
                )
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

    def align_time_stamps(
        self,
        freq: str = "1h",
        method: str = "time",
    ):
        """
        Aligns timestamps to occur on the hour. E.g., 01:00 not 01:05.

        Uses the TimeStampAligner class.

        Parameters
        ----------
        method : str, optional
            method to use for shifting, defaults to shifting to nearest
            hour, by default "time"
        freq : str, optional
            Define how regular the timestamps should be, 1 hour by
            default, by default "1H"
        """
        if self.config.time_resolution:
            freq = self.config.time_resolution

        try:
            timestamp_aligner = TimeStampAligner(self.data_frame)
        except Exception as e:
            message = (
                "Could not align timestamps of dataframe. First the "
                "dataframe must have a date time index.\n"
                f"Exception: {e}"
            )
            print(message)
            core_logger.error(message)
        timestamp_aligner.align_timestamps(
            freq=freq,
            method=method,
        )
        self.data_frame = timestamp_aligner.return_dataframe()

    def date_time_as_index(
        self,
    ) -> pd.DataFrame:
        """
        Sets a date_time column as the index of the contained DataFrame

        Returns:
            pd.DataFrame: data with a DatetimeIndex
        """

        date_time_column = self.extract_date_time_column()
        date_time_column = self.convert_time_zone(date_time_column)
        self.data_frame.index = date_time_column
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

    def aggregate_data_frame(self):
        """TODO"""
        pass

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
            message = f"Failed trying to process thermal_neutron_counts. {e}"
            core_logger.error(message)

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
        if neutron_column_type == InputColumnDataType.EPI_NEUTRON_COUNT:
            raw_column_name = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)
            final_column_name = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)
        elif neutron_column_type == InputColumnDataType.THERM_NEUTRON_COUNT:
            raw_column_name = str(ColumnInfo.Name.THERM_NEUTRON_COUNT_RAW)
            final_column_name = str(ColumnInfo.Name.THERM_NEUTRON_COUNT_CPH)

        epi_neutron_cols = [
            col
            for col in self.config.column_data
            if col.variable_type is neutron_column_type
        ]

        epi_neutron_unit = next(
            col.unit
            for col in self.config.column_data
            if col.variable_type is neutron_column_type
        )

        if len(epi_neutron_cols) > 1:
            epi_col_names = [name.initial_name for name in epi_neutron_cols]

            self.data_frame[raw_column_name] = self.data_frame[
                epi_col_names
            ].sum(axis=1)
        else:
            epi_col_name = epi_neutron_cols[0].initial_name
            self.data_frame.rename(
                columns={epi_col_name: raw_column_name},
                inplace=True,
            )

        if epi_neutron_unit == "counts_per_hour":
            self.data_frame[final_column_name] = self.data_frame[
                raw_column_name
            ]
        elif epi_neutron_unit == "absolute_count":
            self.data_frame[final_column_name] = (
                self.data_frame[raw_column_name]
                * self.config.conversion_factor_to_counts_per_hour
            )
        elif epi_neutron_unit == "counts_per_second":
            self.data_frame[final_column_name] = (
                self.data_frame[raw_column_name] * 3600
            )

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
        self.data_frame_to_numeric()
        self.prepare_key_columns()
        return self.data_frame


class TimeStampAligner:
    """
    Uses routines from SaQC to align the time stamps of the data to a
    common set. When data is read in it is added to an SaQC object which
    is stored as an internal feature. Data can then be aligned and
    converted back to a pd.DataFrame.

    Example
    -------
    >>> import pandas as pd
    >>> from neptoon.data_ingest_and_formatting.timestamp_alignment import (
    ...    TimeStampAligner
    ... )
    >>> data = {'value': [1, 2, 3, 4]}
    >>> index = pd.to_datetime(
    ...     [
    ...         "2021-01-01 00:04:00",
    ...         "2021-01-01 01:10:00",
    ...         "2021-01-01 02:05:00",
    ...         "2021-01-01 02:58:00",
    ...     ]
    ... )
    >>> df = pd.DataFrame(data, index=index)
    >>> # Initialize the TimeStampAligner
    >>> time_stamp_aligner = TimeStampAligner(df)
    >>> # Align timestamps
    >>> time_stamp_aligner.align_timestamps(method='nshift', freq='1H')
    >>> # Get the aligned dataframe
    >>> aligned_df = time_stamp_aligner.return_dataframe()
    >>> print(aligned_df)
    """

    def __init__(self, data_frame: pd.DataFrame):
        """
        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame containing time series data.
        """
        self._validate_timestamp_index(data_frame)
        self.data_frame = data_frame
        self.qc = SaQC(self.data_frame, scheme="simple")

    def _validate_timestamp_index(self, data_frame):
        """
        Checks that the index of the dataframe is timestamp (essential
        for aligning the time stamps and using SaQC)

        Parameters
        ----------
        data_frame : pd.DataFrame
            The data frame imported into the TimeStampAligner

        Raises
        ------
        ValueError
            If the index is not datetime type
        """
        if not pd.api.types.is_datetime64_any_dtype(data_frame.index):
            raise ValueError("The DataFrame index must be of datetime type")

    @log_key_step("method", "freq")
    def align_timestamps(self, freq: str = "1h", method: str = "time"):
        """
        Aligns the time stamp of the SaQC feature. Will automatically do
        this for all data columns. For more information on the values
        for method and freq see:

        https://rdm-software.pages.ufz.de/saqc/

        Parameters
        ----------
        method : str, optional
            Defaults to the nearest shift method to align time stamps.
            This means data is adjusted to the nearest time stamp
            without interpolation, by default "time".
        freq : str, optional
            The frequency of time stamps wanted, by default "1Hour"
        """

        self.qc = self.qc.align(
            field=self.data_frame.columns,
            freq=freq,
            method=method,
        )

    def return_dataframe(self):
        """
        Returns a pd.DataFrame from the SaQC object. Run this after
        alignment to return the aligned dataframe

        Returns
        -------
        df: pd.DataFrame
            DataFrame of time series data
        """
        df = self.qc.data.to_pandas()
        return df


class CollectAndParseRawData:
    """
    Central class which allows us to do the entire ingest and
    formatting routine. Designed to work with a YAML file.
    """

    def __init__(
        self,
        path_to_yaml: Union[str, Path],
        file_collection_config: FileCollectionConfig = None,
        input_formatter_config: InputDataFrameFormattingConfig = None,
    ):
        self._path_to_yaml = validate_and_convert_file_path(path_to_yaml)
        self.file_collection_config = file_collection_config
        self.input_formatter_config = input_formatter_config

    @property
    def path_to_yaml(self):
        return self._path_to_yaml

    @path_to_yaml.setter
    def path_to_yaml(self, new_path):
        return validate_and_convert_file_path(new_path)

    def create_data_frame(self):
        self.file_collection_config = FileCollectionConfig(self.path_to_yaml)
        self.file_collection_config.build_from_yaml()
        file_manager = ManageFileCollection(config=self.file_collection_config)
        file_manager.get_list_of_files()
        file_manager.filter_files()
        file_parser = ParseFilesIntoDataFrame(
            file_manager=file_manager, config=self.file_collection_config
        )
        parsed_data = file_parser.make_dataframe()

        self.input_formatter_config = InputDataFrameFormattingConfig(
            path_to_yaml=self.path_to_yaml
        )
        self.input_formatter_config.import_yaml()
        self.input_formatter_config.build_from_yaml()
        data_formatter = FormatDataForCRNSDataHub(
            data_frame=parsed_data,
            config=self.input_formatter_config,
        )
        df = data_formatter.format_data_and_return_data_frame()
        return df
