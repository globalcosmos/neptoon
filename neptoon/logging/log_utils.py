from pathlib import Path


def get_default_log_path():
    """
    Function for finding the default log file location

    Returns
    -------
    pathlib.Path
        The full Path (including filename) of the default log file
    """
    return Path.home() / ".neptoon" / "logs" / "core_log.log"


def get_log_path():
    """
    Function for finding the main log file location

    Returns
    -------
    pathlib.Path
        The full Path (including filename) of the log file
    """
    try:
        from neptoon.config.global_configuration import GlobalConfig

        cache_file_path = GlobalConfig.get_cache_dir()
        return cache_file_path / "logs" / "core_log.log"
    except ImportError:
        return get_default_log_path()
