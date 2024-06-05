"""
"""

import os
import pandas as pd
import tarfile
import zipfile
import io
from pathlib import Path
from typing import Union
from glob import glob1  # filter file names in folders
from datetime import datetime, timezone, timedelta

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
        encoding="cp850",
        skip_lines: int = 0,
        seperator: str = ",",
        decimal: str = ".",
        parser_kw: dict = dict(
            # These could be defined in a specific YAML file
            strip_left=True,
            digit_first=True,
        ),
    ):
        self._data_location = self._validate_and_convert_data_location(
            data_location=data_location
        )
        self._prefix = prefix
        self._encoding = encoding
        self._skip_lines = skip_lines
        self._parser_kw = parser_kw
        self._seperator = seperator
        self._decimal = decimal
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
    def encoding(self):
        return self._encoding

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
        if self.folder_location.is_dir():
            self.folder_or_archive = "folder"
            core_logger.info("Extracting data from a folder")
        elif tarfile.is_tarfile(self.folder_location):
            self.folder_or_archive = "tarfile"
            core_logger.info("Extracting data from a tarfile")
        elif zipfile.is_zipfile(self.folder_location):
            self.folder_or_archive = "zipfile"
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
        if self.folder_location.is_dir():
            try:
                item_list = self.folder_location.glob("**/*")
                files = [x for x in item_list if x.is_file()]

            except FileNotFoundError as fnf_error:
                message = (
                    f"! Folder not found: {self.folder_location}."
                    f"Error: {fnf_error}"
                )
                core_logger.error(message)
                raise
            except Exception as err:
                message = (
                    f"! Error accessing folder {self.folder_location}."
                    f" Error: {err}"
                )
                core_logger.error(message)
                raise

        return files

    def _return_list_of_files_from_zip(self) -> list:
        """
        Returns a list of files from an zip.

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
        Returns a list of files from an tar.

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
        prefix: str = "",
        suffix: str = "",
        # TODO maybe add regexp or * functionality
    ) -> list:
        """
        Filter a list of files based on a given pattern.

        Args:
            prefix (str, optional): start of file name. Defaults to "".
            suffix (str, optional): end of file name. Defaults to "".
            verbose (bool, optional): Print number of files filtered. Defaults to True.

        Returns:
            list: filtered list of file names that matched the pattern.
        """
        # Start with ...
        files_filtered = [
            filename for filename in self.files if filename.startswith(prefix)
        ]
        # End with ...
        files_filtered = [
            filename
            for filename in files_filtered
            if filename.endswith(suffix)
        ]
        self.files = files_filtered

        """# # Output
        # if verbose:
        #     print(
        #         "i Files matched the pattern: {:.0f} out of {:.0f}.".format(
        #             len(files_filtered), len(files)
        #         )
        #     )
"""


class ParseFilesIntoDataFrame:
    def __init__(self, file_manager: ManageFileCollection):
        self.file_manager = file_manager

    def merge_files(
        self,
    ) -> str:
        """
        Reads all selected files in a folder or archive,
        applies a basic parsing of the lines using `parse_file_line()`,
        and merges all valid lines into a single large data string.

        Args:
            folder_or_archive (str): either folder path or archive filename
            files (list): list of file names to read
            encoding (str, optional): Decode text. Defaults to "cp850".
            skip_lines (int, optional): Skip first lines per file. Defaults to 0.
            verbose (bool, optional): Print progress. Defaults to True.
            parser_kw (dict, optional): Keywords for `parse_file_line()`. Defaults to dict( strip_left=True, digit_first=True ).

        Returns:
            str: A single large string containing all data lines

        Example:
            merge_files("archive.zip", ["a.csv", "b.csv"])
        """
        data_str = ""
        for filename in self.file_manager.files:
            data_str += self._process_file(filename)

    def _process_file(self, filename):
        """_summary_

        Returns
        -------
        _type_
            _description_
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

    def infer_column_names(
        self,
        filename: str,
        startswith: any = "",
        multiheader: bool = False,  # look for multiple lines
        strip_names: bool = True,
        remove_prefix: str = "//",
    ) -> list:
        """
        Reads a file and tries to infer the column headers.

        Parameters
        ----------
        filename : str
            name of the file to read
        seperator : str, optional
            column separator, by default ","
        startswith : any, optional
            headers start with a string, can be a list of multiple
            strings. by default ""
        multiheader : bool, optional
            look for more than one headers which will eventually be
            joined, by default False
        remove_prefix : str, optional
            _description_, by default "//"

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

                    if line.startswith(startswith):
                        # headers must start with certain letters
                        # Uses the first line if no letter given

                        headers.append(line)

                        if not multiheader:
                            # Stops after first found header, else browse the whole file
                            break

        # Join multiheaders and create a joint list
        header_line = self.file_manager.seperator.join(headers)
        header_list = header_line.split(self.file_manager.seperator)
        if strip_names:
            header_list = [s.strip() for s in header_list]
        if remove_prefix != "":
            header_list = [s.removeprefix(remove_prefix) for s in header_list]

        return header_list

    def make_dataframe(
        self,
        data_str: str,
        column_names: list = None,
        skipinitialspace: bool = True,
    ) -> pd.DataFrame:
        """
        Reads in a string and converts it to a DataFrame.

        Args:
            data_str (str): A multiline string previously read from merged files.
            column_names (list, optional): Names of the columns. Defaults to None.
            skipinitialspace (bool, optional): Skip initial spaces. Defaults to True.

        Returns:
            pd.DataFrame: DataFrame
        """
        if column_names is None:
            column_names = self.infer_column_names()
        # Convert string to DataFrame
        data = pd.read_csv(
            io.StringIO(data_str),
            names=column_names,
            encoding=self.file_manager.encoding,
            skiprows=self.file_manager.skip_lines,
            skipinitialspace=skipinitialspace,
            sep=self.file_manager.seperator,
            decimal=decimal,
            on_bad_lines="skip",  # ignore all lines with bad columns
            dtype=object,  # Allows for reading strings
        )

        return data


class FormatDataForCRNSDataHub:

    def make_datetime(
        data: pd.DataFrame,
        columns=0,  # Can be int, column_name, or a list these
        fmt: str = None,
        tz: str = "utc",
        tz_convert: str = "utc",
        timestamp: bool = False,
        dt_column: str = "_datetime",
    ) -> pd.DataFrame:
        """_summary_
        Create a Datetime column, merge columns if necessary.

        Args:
            data (pd.DataFrame): data
            columns (int, optional): column index, column name, or list of these. Defaults to 0.
            fmt (str, optional): Datetime format, or guess. Defaults to None.
            tz (str, optional): Initial time zone. Defaults to "utc".
            tz_convert (str, optional): Timezone to convert to. Defaults to "utc".
            timestamp (bool, optional): Is the initial format a timestamp? Defaults to False.
            dt_column (str, optional): New datetime column name. Defaults to "_datetime".

        Returns:
            pd.DataFrame: data including a Datetime column.
        """
        # Define the index column
        if isinstance(columns, int):
            dt_series = data.iloc[:, columns]
        elif isinstance(columns, str):
            dt_series = data[columns]
        elif isinstance(columns, list):
            # Join multiple columns
            column_names = []
            for i in columns:
                if isinstance(i, int):
                    column_names.append(data.columns[i])
                elif isinstance(i, str):
                    column_names.append(data[i])
            # Join columns together separated with a space
            dt_series = data[column_names].apply(
                lambda x: "{} {}".format(x[0], x[1]), axis=1
            )

        data[dt_column] = pd.to_datetime(
            dt_series,
            errors="coerce",
            unit="s" if timestamp else None,
            format=fmt,
        )

        # Convert time zones
        if (
            data[dt_column][0].tzinfo is None
        ):  # or d.tzinfo.utcoffset(d) is None
            data[dt_column] = data[dt_column].dt.tz_localize(tz)
        if tz_convert != tz:
            data[dt_column] = data[dt_column].dt.tz_convert(tz_convert)

        return data

    def datetime_as_index(
        data: pd.DataFrame,
        dt_column: str = "_datetime",
        drop_nan: bool = True,
        sort: bool = True,
        drop_duplicates: bool = True,
        drop_future: bool = True,
        verbose: bool = True,
    ) -> pd.DataFrame:
        """_summary_
        Set a datetime column as the index of the DataFrame
        Args:
            data (pd.DataFrame): data
            dt_column (str, optional): Name of the datetime column. Defaults to "_datetime".
            drop_nan (bool, optional): Drop invalid datetimes. Defaults to True.
            sort (bool, optional): Sort the index. Defaults to True.
            drop_duplicates (bool, optional): Drop duplicate datetimes. Defaults to True.
            drop_future (bool, optional): Drop datetimes in the future. Defaults to True.
            verbose (bool, optional): Report about droppings. Defaults to True.

        Returns:
            pd.DataFrame: data with a DatetimeIndex
        """

        # Quality checks
        len_0 = len(data)
        if drop_nan:
            # Remove NaT
            data = data.dropna(subset=[dt_column])

        # Set as index
        data.set_index(dt_column, inplace=True)

        if sort:
            data = data.sort_index()

        len_1 = len(data)
        if drop_duplicates:
            data = data[~data.index.duplicated(keep="first")]

        len_2 = len(data)
        if drop_future:
            # remove dates in the future
            data = data[
                data.index <= datetime.now(timezone.utc) + timedelta(1)
            ]

        len_3 = len(data)
        if verbose and 0 < len_0 - len_1 + len_1 - len_2 + len_2 - len_3:
            print(
                "i Dropped indices: {:} invalid, {:} duplicated, {:} in the future.".format(
                    len_0 - len_1, len_1 - len_2, len_2 - len_3
                )
            )
        return data

    def dataframe_to_numeric(
        data: pd.DataFrame,
        decimal: str = ".",
    ):
        """_summary_
        Convert DataFrame to numeric values

        Args:
            data (pd.DataFrame): data
            decimal (str, optional): Decimal character. Defaults to ".".
        """
        # Cases when decimal is not ., replace them by .
        decimal = decimal.strip()
        if decimal != ".":
            data = data.apply(lambda x: x.str.replace(decimal, "."))

        # Convert all the regular columns to numeric and drop any failures
        data = data.apply(pd.to_numeric, errors="coerce")

        return data
