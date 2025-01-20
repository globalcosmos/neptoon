import logging
from functools import wraps
from inspect import signature
from pathlib import Path
from typing import Union
import yaml
import hashlib
import time

from neptoon.logging import get_logger


core_logger = get_logger()

"""
IDEAS:

The DataAuditLog is currently named by the user and a warning tells the
user when multiple logs of same name are shown (it would add logging to
old file). Perhaps in the final form it uses a universal name and gets
auto deleted when it is parsed into a YAML. That way the DataAuditLog
only there for the instance? For now I'll leave in the naming part but
perhaps do this.
"""


def log_key_step(*log_args):
    """
    Decorator which is used to record functions and values used in such
    functions.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data_audit_log = DataAuditLog.get_instance()
            except Exception as e:
                core_logger.warning(
                    f"No DataAuditLog found: {e}/n"
                    "No DataAuditLog taking place"
                )
                data_audit_log = None

            if data_audit_log is not None:
                sig = signature(func)
                bound_arguments = sig.bind(*args, **kwargs)
                bound_arguments.apply_defaults()

                func_name = func.__name__
                if func_name == "__init__":
                    class_name = args[0].__class__.__name__
                    func_name = class_name

                data_audit_log_info = {
                    arg: bound_arguments.arguments[arg]
                    for arg in log_args
                    if arg in bound_arguments.arguments
                }

                data_audit_log.add_step(func_name, data_audit_log_info)

            return func(*args, **kwargs)

        return wrapper

    return decorator


class DataAuditLog:
    """
    The DataAuditLog in a singleton pattern
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern to ensure only one DataAuditLog is created at
        any one time. When instantiated it uses the init_data_audit_log
        method for creation.
        """

        if cls._instance is None:
            cls._instance = super(DataAuditLog, cls).__new__(cls)
        return cls._instance

    @classmethod
    def create(cls):
        """
        Creates a unique DataAuditLog instance with a specific filename.
        """
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.init_data_audit_log()
        else:
            message = (
                "DataAuditLog instance already exists.\n "
                "Only one instance should be created for each\n"
                "processing run."
                "Use DataAuditLog.delete_instance() to remove it\n"
                "prior to running a new site."
            )
            core_logger.warning(message)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls._instance

    @classmethod
    def delete_instance(cls):
        if cls._instance:
            cls._instance.close_log()
            cls._instance = None
        else:
            raise Exception("No instance exists for deletion")

    @classmethod
    def delete_log_file(cls):
        if cls._instance:
            cls._instance.file_delete()
        else:
            raise Exception("Could not find file for deletion")

    @classmethod
    def get_log_file_path(cls):
        if cls._instance and hasattr(cls._instance, "log_file_path"):
            return cls._instance.log_file_path
        else:
            core_logger.warning("No log_file_path available")

    @classmethod
    def create_log_folder(
        cls, site_name: str, custom_log_location: Union[Path, None] = None
    ):
        if cls._instance and hasattr(cls._instance, "log_file_path"):
            if site_name is None:
                raise Exception("You must select a name for the log.")
            timestamp = time.strftime("%Y-%m-%d %H-%M-%S")

            folder_name = f"{site_name} {timestamp}"
            if custom_log_location is None:
                log_location = Path.cwd()
            else:
                log_location = custom_log_location
            archive_folder = Path(
                log_location / "data_audit_log" / folder_name
            )
            archive_folder.mkdir(parents=True, exist_ok=True)
            cls._instance.archive_folder_location = archive_folder

    @classmethod
    def archive_data_audit(cls, site_name=None, custom_log_location=None):
        cls._instance.create_log_folder(
            site_name=site_name, custom_log_location=custom_log_location
        )

        archive_folder = cls._instance.archive_folder_location

        yaml_string = ParseDataAuditLog.parse_log_to_yaml_string(
            log_file_path=cls._instance.get_log_file_path()
        )
        yaml_hash = ParseDataAuditLog.hash_yaml_string(yaml_string=yaml_string)
        save_hash = archive_folder / "hash.txt"
        save_hash.write_text(yaml_hash)

        ParseDataAuditLog.save_yaml_string_to_file(
            yaml_string=yaml_string, yaml_save_location=archive_folder
        )

    @classmethod
    def archive_and_delete_log(cls, site_name=None, custom_log_location=None):
        cls._instance.archive_data_audit(
            site_name=site_name, custom_log_location=custom_log_location
        )
        cls._instance.delete_log_file()
        cls._instance.delete_instance()

    def init_data_audit_log(self):
        self.log_file_path = Path.cwd() / "DataAuditLog.log"
        self.logger = logging.getLogger("DataAuditLog")
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        data_audit_log_handler = logging.FileHandler(self.log_file_path)
        formatter = logging.Formatter("%(message)s")
        data_audit_log_handler.setFormatter(formatter)
        self.logger.addHandler(data_audit_log_handler)
        self.archive_folder_location = None

    def add_step(self, function_name, parameters):
        """
        Adds a record of a processing step to the log

        Parameters
        ----------
        function_name : str
            The name of the function being recorded.
        parameters : dict
            The parameters being applied in the function that are set to
            be recorded by the decorator: @key_steps_log()
        """
        params_yaml = parameters

        self.logger.info(
            f"function: {function_name} parameters: {params_yaml}"
        )

    def close_log(self):
        """
        Closes the log handlers attached to the logger.
        """
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

    def file_delete(self):
        """
        Deletes the log file associated with the DataAuditLog
        """
        try:
            self.log_file_path.unlink()
        except PermissionError:
            # TODO: should be a logger message/warning?
            print("Permission error: Log file is used by another process.")


class ParseDataAuditLog:
    """
    Parse the DataAuditLog file into a YAML
    """

    @staticmethod
    def parse_log_to_yaml_string(log_file_path):
        """
        Converts the DataAuditLog log file into a string in the YAML
        format.

        Parameters
        ----------
        log_file_path : pathlib.Path | str
            Path to the log file

        Returns
        -------
        yaml_str
            The log file, as a string, parsed into the YAML style.
        """
        functions_dict = {}
        with open(log_file_path, "r") as file:
            for line in file:
                func_part, params_str = line.split("parameters:")
                function_name = func_part.replace("function:", "").strip()
                params_str = params_str.strip()[1:-1]
                params_pairs = params_str.split(",")

                params_dict = {}
                for pair in params_pairs:
                    key, value = pair.split(":")
                    key = key.replace("'", "")
                    key = key.replace(" ", "")
                    value = value.replace("'", "")
                    value = value.replace(" ", "")
                    if value.replace(".", "", 1).isdigit():
                        value = float(value) if "." in value else int(value)
                    params_dict[key] = value

                if function_name not in functions_dict:
                    functions_dict[function_name] = []
                functions_dict[function_name].append(params_dict)

                # functions_dict[function_name] = params_dict
        yaml_str = yaml.dump(functions_dict)
        return yaml_str

    @staticmethod
    def save_yaml_string_to_file(yaml_string, yaml_save_location):
        with open((yaml_save_location / "audit.yaml"), "w") as yaml_file:
            yaml_file.write(yaml_string)

    @staticmethod
    def hash_yaml_string(yaml_string):
        """
        Creates a SHA256 hash based on the Yaml string provided.

        Parameters
        ----------
        yaml_str : str
            String in YAML style

        Returns
        -------
        SHA256 Hash
            The SHA256 Hash representing the string
        """
        return hashlib.sha256(yaml_string.encode("utf-8")).hexdigest()
