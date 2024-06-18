"""
TODO: infer_column_names still has some parameter options to add. add
these to the ManageFileCollection object?

TODO: 
"""

import pandas as pd
import tarfile
import zipfile
import io
from saqc import SaQC
from pathlib import Path
from typing import Union
from glob import glob1  # filter file names in folders
from datetime import datetime, timezone, timedelta
from neptoon.data_management.data_audit import log_key_step
from neptoon.logging import get_logger

core_logger = get_logger()


class ManageFileCollection:
    """
    Manages the collection of files in preperation for parsing them into
    a DataFrame for the CRNSDataHub.

    Example:
    --------
    >>> from neptoon.data_ingest_and_formatting.data_ingest import ManageFileCollection
    >>> data_location_folder = "/path/to/folder"
    >>> file_manager = ManageFileCollection(data_location_folder)
    >>> file_manager.get_list_of_files()
    """

    def __init__(
        self,
        data_location: Union[str, Path],
        prefix=None,
        suffix=None,
        encoding="cp850",
        skip_lines: int = 0,
        seperator: str = ",",
        decimal: str = ".",
        skipinitialspace: bool = True,
        parser_kw: dict = dict(
            # These could be defined in a specific YAML file
            strip_left=True,
            digit_first=True,
        ),
    ):
        """
        Initial parameters for data collection and merging

        Parameters
        ----------
        data_location : Union[str, Path]
            The location of the data files. Can be either a string
            representing folder/file location or a Path object (it will
            be converted to a Path object if a string is presented).
        prefix : str, optional
            start of file name - used for file filtering, by default
            None
        suffix : str, optional
            end of file name - used for file filtering, by default None
        encoding : str, optional
            encoder used for file encoding, by default "cp850"
        skip_lines : int, optional
            Whether lines should be skipped when parsing files, by
            default 0
        seperator : str, optional
            The default seperator used to divide columns, by default ","
        decimal : str, optional
            The default decimal character for floating point numbers ,
            by default "."
        skipinitialspace : bool, optional
            whether to skip intial space when creating dataframe, by
            default True
        parser_kw : dict, optional
            dictionary with parser values to use when parsing data, by
            default
            dict(
                strip_left=True,
                digit_first=True,
                )
        """
        self._data_location = self._validate_and_convert_data_location(
            data_location=data_location
        )
        self._prefix = prefix
        self._suffix = suffix
        self._encoding = encoding
        self._skip_lines = skip_lines
        self._parser_kw = parser_kw
        self._seperator = seperator
        self._decimal = decimal
        self._skipinitialspace = skipinitialspace
        self._source_type = None
        self.files = []

        # init functions
        self._determine_source_type()

    @property
    def data_location(self):
        return self._data_location

    @property
    def prefix(self):
        return self._prefix

    @property
    def suffix(self):
        return self._suffix

    @property
    def encoding(self):
        return self._encoding

    @property
    def skipinitialspace(self):
        return self._skipinitialspace

    @property
    def decimal(self):
        return self._decimal

    @property
    def skip_lines(self):
        return self._skip_lines

    @property
    def parser_kw(self):
        return self._parser_kw

    @property
    def seperator(self):
        return self._seperator

    @property
    def source_type(self):
        return self._source_type

    @source_type.setter
    def source_type(self, value: str):
        self._source_type = value

    def _validate_and_convert_data_location(
        self, data_location: Union[str, Path]
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
        if isinstance(data_location, str):
            return Path(data_location)
        elif isinstance(data_location, Path):
            return data_location
        else:
            message = (
                "data_location must be of type str or pathlib.Path. \n"
                f"{type(data_location).__name__} provided, "
                "please change this."
            )
            core_logger.error(message)
            raise ValueError(message)

    def _determine_source_type(self):
        """
        Checks if the folder is a normal folder or an archive and sets
        the internal attribute reflecting this.
        """
        if self.data_location.is_dir():
            self.source_type = "folder"
            core_logger.info("Extracting data from a folder")
        elif tarfile.is_tarfile(self.data_location):
            self.source_type = "tarfile"
            core_logger.info("Extracting data from a tarfile")
        elif zipfile.is_zipfile(self.data_location):
            self.source_type = "zipfile"
        else:
            # TODO logging?
            print(
                "! Cannot read files, the source is neither a folder nor an archive."
            )
            return ""

    def _return_list_of_files_from_folder(self) -> list:
        """
        Returns the list of files from a given folder.

        Returns
        -------
        list
            list of files contained in the folder
        """

        files = []
        if self.data_location.is_dir():
            try:
                item_list = self.data_location.glob("**/*")
                files = [x.name for x in item_list if x.is_file()]

            except FileNotFoundError as fnf_error:
                message = (
                    f"! Folder not found: {self.data_location}."
                    f"Error: {fnf_error}"
                )
                core_logger.error(message)
                raise
            except Exception as err:
                message = (
                    f"! Error accessing folder {self.data_location}."
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
            with zipfile.ZipFile(self.data_location, "r") as archive:
                files = archive.namelist()

        except FileNotFoundError as fnf_error:
            message = (
                f"! Archive file not found: {self.data_location}."
                f"Error: {fnf_error}"
            )

            raise
        except Exception as err:
            message = (
                f"! Error accessing archive {self.data_location}. "
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
            with tarfile.TarFile(self.data_location, "r") as archive:
                files = archive.getnames()

        except FileNotFoundError as fnf_error:
            message = (
                f"! Archive file not found: {self.data_location}."
                f"Error: {fnf_error}"
            )

            raise
        except Exception as err:
            message = (
                f"! Error accessing archive {self.data_location}. "
                f"Error: {err}"
            )
            core_logger.error(message)
            raise

        return files

    def get_list_of_files(self):
        """
        Lists the files found at the data_source and assigns these to
        the file attribute.
        """
        if self.source_type == "folder":
            self.files = self._return_list_of_files_from_folder()
        elif self.source_type == "zipfile":
            self.files = self._return_list_of_files_from_zip()
        elif self.source_type == "tarfile":
            self.files = self._return_list_of_files_from_tar()
        else:
            message = (
                "Data source appears to not be folder, zip or tar file.\n"
                "Cannot collect file names."
            )
            core_logger.error(message)
        
        
    def filter_files(
        self,
    ) -> list:
        """
        Filters the files found in the data location using the prefix or
        suffix given during initialisation. Both of these default to
        None.

        TODO maybe add regexp or * functionality
        """
        files_filtered = [
            filename
            for filename in self.files
            if filename.startswith(self.prefix)
        ]
        # End with ...
        files_filtered = [
            filename
            for filename in files_filtered
            if filename.endswith(self.suffix)
        ]
        self.files = files_filtered


class ParseFilesIntoDataFrame:
    """
    Take's an instance of the ManageFileColletion class which defines
    data location and parsing parameters. Uses this to parse the raw
    files into a single dataframe.

    Example
    -------
    >>> file_manager = ManageFileCollection(data_location='/path/to/data/folder/')
    >>> file_parser = ParseFilesIntoDataFrame(file_manager)
    >>> df = file_parser.make_dataframe()
    """

    def __init__(
        self,
        file_manager: ManageFileCollection,
        startswith: any = "",
        multiheader: bool = False,  # look for multiple lines
        strip_names: bool = True,
        remove_prefix: str = "//",
    ):
        """
        Initialisation files.

        Parameters
        ----------
        file_manager : ManageFileCollection
            An instance fo the ManageFileCollection class
        seperator : str, optional
            column separator, by default ","
        startswith : any, optional
            headers start with a string, can be a list of multiple
            strings. by default ""
        multiheader : bool, optional
            look for more than one headers which will eventually be
            joined, by default False
        remove_prefix : str, optional
            remove first characters of a line, by default "//"
        """
        self.file_manager = file_manager
        self._startswith = startswith
        self._multiheader = multiheader
        self._strip_names = strip_names
        self._remove_prefix = remove_prefix

    @property
    def startswith(self):
        return self._startswith
    @property
    def multiheader(self):
        return self._multiheader
    @property
    def strip_names(self):
        return self._strip_names
    @property
    def remove_prefix(self):
        return self._remove_prefix

    def make_dataframe(
        self,
        column_names: list = None,
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
            column_names = self._infer_column_names()

        data_str = self.merge_files()
        data = pd.read_csv(
            io.StringIO(data_str),
            names=column_names,
            encoding=self.file_manager.encoding,
            skiprows=self.file_manager.skip_lines,
            skipinitialspace=self.file_manager.skipinitialspace,
            sep=self.file_manager.seperator,
            decimal=self.file_manager.decimal,
            on_bad_lines="skip",  # ignore all lines with bad columns
            dtype=object,  # Allows for reading strings
        )

        return data

    def _merge_files(
        self,
    ) -> str:
        """
        Reads all selected files in a folder or archive, applies a basic
        parsing of the lines using `_parse_file_line()`, and merges all
        valid lines into a single large data string.

        Returns
        -------
        str
            A single large string containing all data lines
        """
        data_str = ""
        for filename in self.file_manager.files:
            data_str += self._process_file(filename)

    def _process_file(self, filename):
        """
        Opens file and extracts each file line into a large data string.

        Returns
        -------
        data_str: str
            Returns a large string containing data
        """
        data_str = ""

        with self._open_file(filename, self.data_manager.encoding) as file:

            for _ in range(self.data_manager.skip_lines):
                next(file)
            for line in file:
                data_str += self._parse_file_line(
                    line,
                )

        return data_str

    def _open_file(self, filename):
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

        if self.data_manager.source_type == "folder":
            return open(
                self.data_manager.data_location / filename,
                encoding=self.file_manager.encoding,
            )
        elif self.data_manager.source_type == "tarfile":
            archive = tarfile.open(self.file_manager.data_location, "r")
            return archive.extractfile(filename)
        elif self.data_manager.source_type == "zipfile":
            archive = zipfile.ZipFile(self.file_manager.data_location, "r")
            return archive.open(filename)
        else:
            message = (
                "Unsupported data type at source folder. It must be "
                "a folder, zipfile, or tarfile."
            )
            core_logger.error(message)

    def _parse_file_line(
        self,
        line: str,
    ) -> str:
        """
        Parses a single line

        Args:
            line (str): line of potential data
            encoding (str, optional): How to decode. Defaults to "cp850".
            strip_left (bool, optional): Remove starting spaces. Defaults to True.
            digit_first (bool, optional): Valid data always starts with a digit. Defaults to True.

        Returns:
            str: a valid line or an empty string
        """
        if self.file_manager.parser_kw["strip_left"]:
            line = line.lstrip()

        if isinstance(line, bytes) and self.data_manager.encoding != "":
            line = line.decode(self.data_manager.encoding, errors="ignore")

        # If the line starts with a number, it likely is actual data
        if (
            self.file_manager.parser_kw["digit_first"]
            and not line[:1].isdigit()
        ):
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
            self.file_manager.files[0], self.data_manager.encoding
        ) as file:

            for _ in range(self.file_manager.skip_lines):
                next(file)

            headers = []
            for line in file:
                if self.file_manager.seperator in line:
                    # headers must contain at least one separator

                    if line.startswith(self.startswith):
                        # headers must start with certain letters
                        # Uses the first line if no letter given

                        headers.append(line)

                        if not self.multiheader:
                            # Stops after first found header, else browse the whole file
                            break

        # Join multiheaders and create a joint list
        header_line = self.file_manager.seperator.join(headers)
        header_list = header_line.split(self.file_manager.seperator)
        if self.strip_names:
            header_list = [s.strip() for s in header_list]
        if self.remove_prefix != "":
            header_list = [s.removeprefix(self.remove_prefix) for s in header_list]

        return header_list

# Concept
# formatter = FormatDataForCRNSDataHub(df)
# formatter.format_data_frame()
# df = formatter.return_data_frame()
# formats reduces the df to the main columns, use this column, average those columns
# crnsdatahub = CRNSDataHub(df) # expectes certain format
# validation
# quality checks
# crnsdatahub.align_time()

class FormatDataForCRNSDataHub:
    """
    TODO datetime column has two very similar version. Need to fix this.
    TODO double check extract_datetime_column for logic
    TODO Other formatting??
    TODO One Click Function that compiles the formatting
    """

    def __init__(
        self,
        data_frame: pd.DataFrame,
        columns=0,  # Can be int, column_name, or a list these
        datetime_format: str = None,
        initial_time_zone: str = "utc",
        convert_time_zone_to: str = "utc",
        is_timestamp: bool = False,
        datetime_column: str = "_datetime",
        decimal: str = ".",
    ):
        self._data_frame = data_frame
        self._columns = columns
        self._datatime_format = datetime_format
        self._initial_time_zone = initial_time_zone
        self._convert_time_zone_to = convert_time_zone_to
        self._is_timestamp = is_timestamp
        self._dt_column = datetime_column
        self._decimal = decimal

    @property
    def data_frame(self):
        return self._data_frame

    @property
    def columns(self):
        return self._columns

    @property
    def datetime_format(self):
        return self._datatime_format

    @property
    def initial_time_zone(self):
        return self._initial_time_zone

    @property
    def convert_time_zone_to(self):
        return self._convert_time_zone_to

    @property
    def is_timestamp(self):
        return self._is_timestamp

    @property
    def decimal(self):
        return self._decimal

    @property
    def datetime_column(self):
        return self._data_time_format

    @data_frame.setter
    def data_frame(self, df: pd.DataFrame):
        self._data_frame = df

    def extract_datetime_column(
        self,
    ) -> pd.Series:
        """
        TODO: docstring

        Create a Datetime column, merge columns if necessary.

        Returns:
            pd.DataFrame: data including a Datetime column.
        """

        # Define the index column
        if isinstance(self.columns, int):
            dt_series = self.data_frame.iloc[:, self.columns]
        elif isinstance(self.columns, str):
            dt_series = self.data_frame[self.columns]
        elif isinstance(self.columns, list):
            # Join multiple columns
            column_names = []
            for i in self.columns:
                if isinstance(i, int):
                    column_names.append(self.data_frame.columns[i])
                elif isinstance(i, str):
                    column_names.append(self.data_frame[i])
            # Join columns together separated with a space
            dt_series = self.data_frame[column_names].apply(
                lambda x: "{} {}".format(x[0], x[1]), axis=1
            )
        dt_series = pd.to_datetime(
            dt_series,
            errors="coerce",
            unit="s" if self.is_timestamp else None,
            format=self.datetime_format,
        )
        return dt_series

    def convert_time_zone(self, datetime_series):
        """
        Convert the timezone of a date time time series. Uses the
        attributes initial_time_zone (the actual time zone the data is
        currently in) and convert_time_zone_to which is the desired time
        zone. This is default set the UTC time.

        Parameters
        ----------
        datetime_series : pd.Series
            The datetime_series that is converted

        Returns
        -------
        pd.Series
            The converted datetime series in the correct time zone
        """
        if datetime_series[0].tzinfo is None:
            datetime_series = datetime_series.dt.tz_localize(
                self.initial_time_zone
            )
        if self.initial_time_zone != self.convert_time_zone_to:
            datetime_series = datetime_series.dt.tz_convert(
                self.convert_time_zone_to
            )
        return datetime_series

    def align_time_stamps(self, method: str = "nshift", freq: str = "1H"):
        """
        Aligns timestamps to occur on the hour. E.g., 01:00 not 01:05.

        Uses the TimeStampAligner class.

        Parameters
        ----------
        method : str, optional
            method to use for shifting, defaults to shifting to nearest
            hour, by default "nshift"
        freq : str, optional
            Define how regular the timestamps should be, 1 hour by
            default, by default "1H"
        """
        try:
            timestamp_aligner = TimeStampAligner(self.data_frame)
        except Exception as e:
            message = (
                "Could not align timestamps of dataframe. First the "
                "dataframe must have a datetime index.\n"
                f"Exception: {e}"
            )
            print(message)
            core_logger.error(message)
        timestamp_aligner.align_timestamps(method=method, freq=freq)
        self.data_frame = timestamp_aligner.return_dataframe()

    def datetime_as_index(
        self,
    ) -> pd.DataFrame:
        """
        Sets a datetime column as the index of the contained DataFrame

        Returns:
            pd.DataFrame: data with a DatetimeIndex
        """

        date_time_column = self.extract_datetime_column()
        date_time_column = self.convert_time_zone()
        self.data_frame.index = date_time_column

    def dataframe_to_numeric(
        self,
    ):
        """
        Convert DataFrame to numeric values.

        """
        # Cases when decimal is not ., replace them by .
        decimal = self.decimal
        decimal = decimal.strip()
        if decimal != ".":
            self.data_frame = self.data_frame.apply(
                lambda x: x.str.replace(decimal, ".")
            )

        # Convert all the regular columns to numeric and drop any failures
        self.data_frame = self.data_frame.apply(pd.to_numeric, errors="coerce")

    def return_data_frame(self):
        """
        Returns the contained DataFrame

        Returns
        -------
        pd.DataFrame
            DataFrame
        """
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
    def align_timestamps(self, method: str = "nshift", freq: str = "1Hour"):
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
            without interpolation, by default "nshift".
        freq : str, optional
            The frequency of time stamps wanted, by default "1Hour"
        """

        self.qc = self.qc.align(
            field=self.data_frame.columns, freq=freq, method=method
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
