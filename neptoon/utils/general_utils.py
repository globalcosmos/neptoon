from pathlib import Path
from typing import Union
from neptoon.logging import get_logger
from datetime import timedelta
import re
import pandas as pd
import numpy as np
import pandera.pandas as pa
import datetime

from neptoon.columns import ColumnInfo

core_logger = get_logger()


def validate_and_convert_file_path(
    file_path: str | Path | None,
    base: str | Path | None = None,
) -> Path:
    """
    Ensures that file paths are correctly parsed into pathlib.Path
    objects.

    Parameters
    ----------
    file_path : str | Path | None
        The path to the folder or file.
    base : str | Path | None
        Base to add to file (e..g, a custom base directory)

    Returns
    -------
    pathlib.Path | None
        The file_path as a pathlib.Path object.

    Raises
    ------
    ValueError
        Error if string, pathlib.Path, or None not given.
    """

    if file_path is None:
        return None

    p = Path(file_path)

    if p.is_absolute() and base is not None:
        message = (
            f"Your filepath ({file_path}) is an absolute path",
            " and you've provided a base path to append. If you want to append "
            "basepath your filepath must be relative (maybe remove the first /?)",
        )

        raise AttributeError(message)

    if p.is_absolute():
        return p.resolve()
    if base:
        p = Path(base) / p

    return p.resolve()


def timedelta_to_freq_str(time_delta: datetime.timedelta) -> str:
    """Convert a timedelta to a pandas frequency string."""
    total_seconds = time_delta.total_seconds()

    if total_seconds % (86400) == 0:  # Days (86400 = 24 * 60 * 60)
        return f"{int(total_seconds // 86400)}D"
    elif total_seconds % 3600 == 0:  # Hours
        return f"{int(total_seconds // 3600)}h"
    elif total_seconds % 60 == 0:  # Minutes
        return f"{int(total_seconds // 60)}min"
    else:  # Seconds
        return f"{int(total_seconds)}S"


def validate_timestamp_index(data_frame):
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


def parse_resolution_to_timedelta(
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

    if unit.lower() in ["min", "mins", "minute", "minutes", "m"]:
        return timedelta(minutes=value)
    elif unit.lower() in ["hour", "hours", "hr", "hrs", "h"]:
        return timedelta(hours=value)
    elif unit.lower() in ["day", "days", "d"]:
        return timedelta(days=value)
    else:
        message = f"Unsupported time unit: {unit}"
        core_logger.error(message)
        raise ValueError(message)


def validate_df(df: pd.DataFrame, schema: pa.DataFrameSchema):
    """
    Validates a df against a pandera.pandas DataFrameSchema

    NOTES:
    Keep it lazy to give info of all df issues

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe to validate
    schema : pa.DataFrameSchema
        Pandera Schema to check against
    """
    return schema.validate(df, lazy=True)


def find_temporal_resolution_seconds(data_frame: pd.DataFrame):

    time_res_seconds = (
        data_frame.index.to_series().dropna().diff().median().total_seconds()
    )
    return time_res_seconds


# def find_median_temporal_resolution_seconds(data_frame: pd.DataFrame):

#     time_res_seconds = (
#         data_frame.index.to_series().dropna().diff().median().total_seconds()
#     )
#     return time_res_seconds


def return_df_with_temporal_resolution_seconds(
    data_frame: pd.DataFrame, column_name=None
):
    data_frame["temp"] = (  # TODO
        data_frame.index.to_series().dropna().diff().total_seconds()
    )
    return data_frame


def is_resolution_greater_than(
    resolution_a: str | datetime.timedelta,
    resolution_b: str | datetime.timedelta,
) -> bool:
    """
    Returns True if resolution_a is greater (coarser) than resolution_b

    Parameters
    ----------
    resolution_a : str | datetime.timedelta
        First resolution to compare
    resolution_b : str | datetime.timedelta
        Second resolution to compare

    Returns
    -------
    bool
        True if resolution_a > resolution_b

    Note
    ----
    If resolution is str then it should be in a form such as "1h",
    "6hour" or "1day". It will be auto converted internally to the func
    """
    if isinstance(resolution_a, str):
        resolution_a = parse_resolution_to_timedelta(resolution_a)
    if isinstance(resolution_b, str):
        resolution_b = parse_resolution_to_timedelta(resolution_b)

    if resolution_a > resolution_b:
        return True
    else:
        return False


def recalculate_neutron_uncertainty(
    data_frame: pd.DataFrame,
    temporal_scaling_factor: int | float,
    uncertainty_col_name: str | None = None,
):
    """
    Adjust the staistical uncertainty of neutrons value based on the
    aggregation.

    Parameters
    ----------
    data_frame : pd.DataFrame
        DataFrame with data
    temporal_scaling_factor : int | float
        The scaling factor to adjust from original resolution to
        revised output resolution
    uncertainty_col_name : str | None, optional
        Name of the col, if None will use the default supplied in
        ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UNCERTAINTY, by
        default None

    Returns
    -------
    _type_
        _description_
    """
    uncertainty_col_name = (
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UNCERTAINTY)
        if uncertainty_col_name is None
        else uncertainty_col_name
    )

    data_frame[uncertainty_col_name] = data_frame[uncertainty_col_name] * (
        1 / np.sqrt(temporal_scaling_factor)
    )
    return data_frame


def is_running_in_docker():
    """
    Checks whether the current kernel is running in a docker container.

    Returns
    -------
    bool
        Whether in docker container
    """
    return Path("/.dockerenv").exists()
