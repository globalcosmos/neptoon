from pathlib import Path
from typing import Union
from neptoon.logging import get_logger

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
