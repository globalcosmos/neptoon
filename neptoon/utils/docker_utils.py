from pathlib import Path


def is_running_in_docker():
    """
    Checks whether the current kernel is running in a docker container.

    Returns
    -------
    bool
        Whether in docker container
    """
    return Path("/.dockerenv").exists()


def return_file_path_with_suffix(base_path: str):
    """
    This is specifically used internally during docker runs. Input data
    is appended as /workingdir/inputdata. This could be a .csv .zip .tar
    or folder. This will check and return name with correct suffix.

    Parameters
    ----------
    base_path : str
        The path to check

    Returns
    -------
    str
        path with suffix

    """
    base_path = Path(base_path)

    for ext in ["", ".zip", ".tar", ".csv"]:
        test_path = base_path.with_suffix(ext) if ext else base_path
        if test_path.exists():
            actual_input_path = str(test_path)
            break
    else:
        actual_input_path = str(base_path)

    return actual_input_path
