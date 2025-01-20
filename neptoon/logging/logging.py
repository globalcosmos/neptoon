import logging
from .log_utils import get_log_path


def configure_logger():
    """
    Configuration steps for the core_logger. This will record errors,
    warnings etc. with time stamps for debugging.

    Returns
    -------
    logging.Logger
        The core logger
    """
    logger = logging.getLogger("global_logger")
    log_file_path = get_log_path()
    log_file_path.parent.mkdir(
        parents=True, exist_ok=True
    )  # Create the directory if it doesn't exist
    logger_handler = logging.FileHandler(log_file_path)
    logger_handler.setLevel(logging.WARNING)
    f_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger_handler.setFormatter(f_format)
    logger.addHandler(logger_handler)
    return logger


logger = configure_logger()


def get_logger():
    """
    Retrieve the logger after it has been instantiated.

    Returns
    -------
    logging.Logger
        The code logger
    """
    return logger
