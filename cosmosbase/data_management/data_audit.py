import logging
from cosmosbase.data_management.logging import get_logger
from pathlib import Path

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
    def create(cls, filename):
        """
        Creates a unique DataAuditLog instance with a specific filename.
        """
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.init_data_audit_log(filename)
        else:
            message = (
                "DataAuditLog instance already exists./n "
                "Only one instance can be created. /n"
                "Use DataAuditLog.delete_instance to remove it"
            )
            core_logger.warning(message)
            raise Exception(message)
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

    def init_data_audit_log(self, filename):
        self.filename = filename + ".log"
        file_path = Path.cwd() / self.filename
        if file_path.exists():
            message = (
                f"A log file called {filename} already "
                "exists in the working directory. It is recommended "
                "to refresh this when making new runs. Use "
                "DataAuditLog.delete_log_file() to do this"
            )
            core_logger.warning(message)

        self.logger = logging.getLogger("DataAuditLog")
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        data_audit_log_handler = logging.FileHandler(self.filename)
        formatter = logging.Formatter("%(message)s")
        data_audit_log_handler.setFormatter(formatter)
        self.logger.addHandler(data_audit_log_handler)

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
        # params_yaml = yaml.dump(parameters)
        params_yaml = parameters

        self.logger.info(
            f"function: {function_name} parameters: {params_yaml}"
        )

    def convert_to_yaml(self):
        pass

    def save_to_yaml(self, filepath):
        pass

    def close_log(self):
        """
        Closes the log handlers attached to the logger.
        """
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)


def log_key_step(*log_args):
    """
    Decorator which is used to record functions and values used in such
    functions.
    """

    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                data_audit_log = DataAuditLog.get_instance()
            except Exception as e:
                core_logger.warning(
                    f"No DataAuditLog found: {e}/n"
                    "No DataAuditLog taking place"
                )
                data_audit_log = None

            if data_audit_log is not None:
                data_audit_log_info = {
                    arg: kwargs.get(arg) for arg in log_args
                }
                data_audit_log.add_step(func.__name__, data_audit_log_info)

            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class ParseDataAuditLog:
    """
    Parse the DataAuditLog file into a YAML
    """

    pass
