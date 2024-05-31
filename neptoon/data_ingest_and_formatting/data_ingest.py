"""
load_data function will be a big logic heavy function to abstract away a
lot of internal checks. The idea is that the same function is used.
"""

import os
import pandas
from glob import glob1  # filter file names in folders
import tarfile  # only needed for unpacking tar files
import zipfile  # only needed for unpacking zip files
from pathlib import Path
import io
from datetime import datetime, timezone, timedelta


def collect_list_of_files_from_folder(path: str) -> list:
    """
    Collects a list of files from a folder.

    Parameters
    ----------
    path : str
        full path of the folder

    Returns
    -------
    list
        list of files contained in the folder
    """

    """
    Collects a list of files from a folder.

    Args:
        path (str): full path of the folder

    Returns:
        list: list of files contained in the folder
    """
    # Open archive
    # TODO What error should we throw when FileNotFoundError?
    files = []
    if os.path.isdir(path):
        try:
            items = os.listdir(path)
            files = [
                item
                for item in items
                if os.path.isfile(os.path.join(path, item))
            ]

        except Exception as err:
            # TODO logging: throw an error?
            print(f"! No files found in folder {path}.")

    return files


def collect_files_from_archive(filename: str) -> list:
    """_summary_
    Collects a list of files from an archive.

    Args:
        filename (str): file name of the archive

    Returns:
        list: list of files contained in the archive
    """
    # Open archive
    # TODO What error should we throw when FileNotFoundError?
    if tarfile.is_tarfile(filename):
        archive = tarfile.TarFile(filename, "r")
    elif zipfile.is_zipfile(filename):
        archive = zipfile.ZipFile(filename, "r")

    # Create list of containing files
    files = []
    try:
        files = archive.namelist()
    except Exception as err:
        # TODO logging: throw an error?
        print(f"! No files found in archive {filename}.")

    if archive:
        archive.close()

    return files


def filter_files(
    files: list,
    prefix: str = "",
    suffix: str = "",
    # TODO maybe add regexp or * functionality
    verbose: bool = True,  # TODO is that a good practice?
) -> list:
    """_summary_
    Filter a list of files based on a given pattern.

    Args:
        files (list): list of file names
        prefix (str, optional): start of file name. Defaults to "".
        suffix (str, optional): end of file name. Defaults to "".
        verbose (bool, optional): Print number of files filtered. Defaults to True.

    Returns:
        list: filtered list of file names that matched the pattern.
    """
    # Start with ...
    files_filtered = [
        filename for filename in files if filename.startswith(prefix)
    ]
    # End with ...
    files_filtered = [
        filename for filename in files_filtered if filename.endswith(suffix)
    ]

    # Output
    if verbose:
        print(
            "i Files matched the pattern: {:.0f} out of {:.0f}.".format(
                len(files_filtered), len(files)
            )
        )

    return files_filtered


def parse_file_line(
    line: str,
    encoding: str = "cp850",
    strip_left: bool = True,
    digit_first: bool = True,
) -> str:
    """_summary_
    Parses a single line

    Args:
        line (str): line of potential data
        encoding (str, optional): How to decode. Defaults to "cp850".
        strip_left (bool, optional): Remove starting spaces. Defaults to True.
        digit_first (bool, optional): Valid data always starts with a digit. Defaults to True.

    Returns:
        str: a valid line or an empty string
    """
    if strip_left:
        line = line.lstrip()

    if isinstance(line, bytes) and encoding != "":
        line = line.decode(encoding, errors="ignore")

    # If the line starts with a number, it likely is actual data
    if digit_first and not line[:1].isdigit():
        return ""

    return line


def guess_header(
    folder_or_archive: str,
    filename: str,
    encoding: str = "cp850",
    sep: str = ",",
    skip_lines: int = 0,
    startswith: any = "",
    multiheader: bool = False,  # look for multiple lines
    strip_names: bool = True,
    remove_prefix: str = "//",
) -> list:
    """_summary_
    Reads a file and tries to find the column headers.

    Args:
        folder_or_archive (str): folder path or archive filename
        filename (str): name of the file to read
        encoding (str, optional): how to decode. Defaults to "cp850".
        sep (str, optional): column separator. Defaults to ",".
        skip_lines (int, optional): lines to skip from top. Defaults to 0.
        startswith (any, optional): headers start with a string, can be a list of multiple strings. Defaults to "".
        multiheader (bool, optional): look for more than one headers which will eventually be joined. Defaults to False.

    Returns:
        list: List of column names
    """
    # Check for folder or archive
    folder = None
    archive = None
    if os.path.isdir(folder_or_archive):
        folder = folder_or_archive
    elif tarfile.is_tarfile(folder_or_archive):
        archive = tarfile.TarFile(folder_or_archive, "r")
    elif zipfile.is_zipfile(folder_or_archive):
        archive = zipfile.ZipFile(folder_or_archive, "r")
    else:
        # TODO logging?
        print(
            "! Cannot read files, the source is neither a folder nor an archive."
        )
        return ""

    # Open file in either folder or archive
    with (
        archive.open(filename, "r")
        if archive
        else open(Path(folder) / filename, encoding=encoding)
    ) as file:

        # Skip first lines
        for _ in range(skip_lines):
            next(file)  # seek to next line

        # Look for header lines
        headers = []
        for line in file:
            if sep in line:
                # headers must contain at least one separator

                if line.startswith(startswith):
                    # headers must start with certain letters
                    # Uses the first line if no letter given

                    headers.append(line)

                    if not multiheader:
                        # Stops after first found header, else browse the whole file
                        break

    # Join multiheaders and create a joint list
    header_line = sep.join(headers)
    header_list = header_line.split(sep)
    if strip_names:
        # Remove spaces around names
        header_list = [s.strip() for s in header_list]
    if remove_prefix != "":
        # Remove spaces around names
        header_list = [s.removeprefix(remove_prefix) for s in header_list]

    return header_list


def merge_files(
    folder_or_archive: str,
    files: list,
    encoding: str = "cp850",
    skip_lines: int = 0,
    verbose: bool = True,
    parser_kw: dict = dict(
        # These could be defined in a specific YAML file
        strip_left=True,
        digit_first=True,
    ),
) -> str:
    """_summary_
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

    # Check for folder or archive
    folder = None
    archive = None
    if os.path.isdir(folder_or_archive):
        folder = folder_or_archive
    elif tarfile.is_tarfile(folder_or_archive):
        archive = tarfile.TarFile(folder_or_archive, "r")
    elif zipfile.is_zipfile(folder_or_archive):
        archive = zipfile.ZipFile(folder_or_archive, "r")
    else:
        # TODO logging?
        print(
            "! Cannot read files, the source is neither a folder nor an archive."
        )
        return ""

    data_str = ""
    len_files = len(files)
    i = 0

    # Loop through filtered files
    for filename in files:
        if verbose:
            print(
                "> {:3.0f}%, {:}".format(i / len_files * 100, filename),
                end="\r",
            )

        # Open file in either folder or archive
        with (
            archive.open(filename, "r")
            if archive
            else open(Path(folder) / filename, encoding=encoding)
        ) as file:

            # Skip first lines
            for _ in range(skip_lines):
                next(file)  # seek to next line

            # Parse the remaining lines
            for line in file:
                data_str += parse_file_line(line, encoding, **parser_kw)
        i += 1

    if archive:
        archive.close()

    if verbose:
        len_filenames = len(max(files, key=len))
        print("> 100%  {:}".format(" " * len_filenames))

    return data_str


def make_dataframe(
    data_str: str,
    column_names: list = None,
    encoding: str = "cp850",
    skip_lines: int = 0,
    skipinitialspace: bool = True,
    sep: str = ",",
    decimal: str = ".",
) -> pandas.DataFrame:
    """_summary_
    Reads in a string and converts it to a DataFrame.

    Args:
        data_str (str): A multiline string previously read from merged files.
        column_names (list, optional): Names of the columns. Defaults to None.
        encoding (str, optional): How to decode. Defaults to "cp850".
        skip_lines (int, optional): Skip lines from top. Defaults to 0.
        skipinitialspace (bool, optional): Skip initial spaces. Defaults to True.
        sep (str, optional): Column separator. Defaults to ",".
        decimal (str, optional): Decimal character. Defaults to ".".

    Returns:
        pandas.DataFrame: DataFrame
    """

    # Convert string to DataFrame
    data = pandas.read_csv(
        io.StringIO(data_str),
        names=column_names,
        encoding=encoding,
        skiprows=skip_lines,
        skipinitialspace=skipinitialspace,
        sep=sep,
        decimal=decimal,
        on_bad_lines="skip",  # ignore all lines will bad columns
        dtype=object,  # Allows for reading strings
    )

    return data


def make_datetime(
    data: pandas.DataFrame,
    columns=0,  # Can be int, column_name, or a list these
    fmt: str = None,
    tz: str = "utc",
    tz_convert: str = "utc",
    timestamp: bool = False,
    dt_column: str = "_datetime",
    # **datetime_kw # pass any parameters to pandas_to_datetime
) -> pandas.DataFrame:
    """_summary_
    Create a Datetime column, merge columns if necessary.

    Args:
        data (pandas.DataFrame): data
        columns (int, optional): column index, column name, or list of these. Defaults to 0.
        fmt (str, optional): Datetime format, or guess. Defaults to None.
        tz (str, optional): Initial time zone. Defaults to "utc".
        tz_convert (str, optional): Timezone to convert to. Defaults to "utc".
        timestamp (bool, optional): Is the initial format a timestamp? Defaults to False.
        dt_column (str, optional): New datetime column name. Defaults to "_datetime".

    Returns:
        pandas.DataFrame: data including a Datetime column.
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

    data[dt_column] = pandas.to_datetime(
        dt_series, errors="coerce", unit="s" if timestamp else None, format=fmt
    )

    # Convert time zones
    if data[dt_column][0].tzinfo is None:  # or d.tzinfo.utcoffset(d) is None
        data[dt_column] = data[dt_column].dt.tz_localize(tz)
    if tz_convert != tz:
        data[dt_column] = data[dt_column].dt.tz_convert(tz_convert)

    return data


def datetime_as_index(
    data: pandas.DataFrame,
    dt_column: str = "_datetime",
    drop_nan: bool = True,
    sort: bool = True,
    drop_duplicates: bool = True,
    drop_future: bool = True,
    verbose: bool = True,
) -> pandas.DataFrame:
    """_summary_
    Set a datetime column as the index of the DataFrame
    Args:
        data (pandas.DataFrame): data
        dt_column (str, optional): Name of the datetime column. Defaults to "_datetime".
        drop_nan (bool, optional): Drop invalid datetimes. Defaults to True.
        sort (bool, optional): Sort the index. Defaults to True.
        drop_duplicates (bool, optional): Drop duplicate datetimes. Defaults to True.
        drop_future (bool, optional): Drop datetimes in the future. Defaults to True.
        verbose (bool, optional): Report about droppings. Defaults to True.

    Returns:
        pandas.DataFrame: data with a DatetimeIndex
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
        data = data[data.index <= datetime.now(timezone.utc) + timedelta(1)]

    len_3 = len(data)
    if verbose and 0 < len_0 - len_1 + len_1 - len_2 + len_2 - len_3:
        print(
            "i Dropped indices: {:} invalid, {:} duplicated, {:} in the future.".format(
                len_0 - len_1, len_1 - len_2, len_2 - len_3
            )
        )
    return data


def dataframe_to_numeric(
    data: pandas.DataFrame,
    decimal: str = ".",
):
    """_summary_
    Convert DataFrame to numeric values

    Args:
        data (pandas.DataFrame): data
        decimal (str, optional): Decimal character. Defaults to ".".
    """
    # Cases when decimal is not ., replace them by .
    decimal = decimal.strip()
    if decimal != ".":
        data = data.apply(lambda x: x.str.replace(decimal, "."))

    # Convert all the regular columns to numeric and drop any failures
    data = data.apply(pandas.to_numeric, errors="coerce")

    return data


def load_data(**kwargs):
    """ """
    pass
