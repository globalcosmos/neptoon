from pathlib import Path
from typing import Union
from neptoon.logging import get_logger
from datetime import timedelta
import re

core_logger = get_logger()


def validate_and_convert_file_path(
    file_path: Union[str, Path, None],
    base: Union[str, Path] = "",
) -> Path:
    """
    Ensures that file paths are correctly parsed into pathlib.Path
    objects.

    Parameters
    ----------
    file_path : Union[str, Path]
        The path to the folder or file.

    Returns
    -------
    pathlib.Path
        The file_path as a pathlib.Path object.

    Raises
    ------
    ValueError
        Error if string, pathlib.Path, or None not given.
    """

    if file_path is None:
        return None
    if isinstance(file_path, str):
        new_file_path = Path(file_path)
        if new_file_path.is_absolute():
            return new_file_path
        else:
            if base == "":
                return Path.cwd() / Path(file_path)
            else:
                return base / Path(file_path)
    elif isinstance(file_path, Path):
        if file_path.is_absolute():
            return file_path
        else:
            if base == "":
                return Path.cwd() / Path(file_path)
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
