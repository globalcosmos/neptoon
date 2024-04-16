from abc import ABC, abstractmethod
import logging
import yaml


class DataAuditLog:
    """
    The Data Audit Log
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
            raise Exception(
                "DataAuditLog instance already exists. Only one instance can be created."
                "Use DataAuditLog.delete_instance to remove it"
            )
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
        self.filename = filename
        ### TODO:
        """
        ADD A CHECK HERE
        add a check for the filename with option to delete log file?
        """
        self.logger = logging.getLogger("DataAuditLog")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(filename)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

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
                log = DataAuditLog.get_instance()
            except:
                logging.warning("No DataAuditLog found")
                log = None

            if log is not None:
                log_info = {arg: kwargs.get(arg) for arg in log_args}
                log.add_step(func.__name__, log_info)

            return func(self, *args, **kwargs)

        return wrapper

    return decorator
