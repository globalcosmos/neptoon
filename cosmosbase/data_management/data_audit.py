from abc import ABC, abstractmethod
import json
import yaml


class DataAuditLogBase(ABC):
    """
    Base class for the DataAuditLog. There are two instances of
    DataAuditLog. The actual DataAuditLog, which is used for logging
    processing steps. The NoOperationDataAuditLog, this is a place
    holder designed to be created when there is no DataAuditLog
    presented.
    """

    def __init__(self):
        self.processing_steps = []

    @abstractmethod
    def add_step(self, *args, **kwargs):
        """
        Add a log step
        """
        pass

    @abstractmethod
    def convert_to_yaml(self):
        """
        Convert to YAML
        """
        pass

    @abstractmethod
    def save_to_yaml(self):
        """
        Save to YAML
        """
        pass


class DataAuditLog(DataAuditLogBase):
    """
    The Data Audit Log
    """

    def add_step(self, function_name, parameters):
        """
        Adds a record of a processing step to the class

        Parameters
        ----------
        function_name : str
            The name of the function being recorded.
        parameters : dict
            The parameters being applied in the function that are set to
            be recorded by the decorator: @key_steps_log()
        """
        self.processing_steps.append(
            {"function": function_name, "parameters": parameters}
        )

    def convert_to_yaml(self):
        """
        Returns a string object in the YAML style

        Returns
        -------
        str
            YAML file of the recorded steps
        """
        return yaml.dump(self.processing_steps, sort_keys=True)

    def save_to_yaml(self, filepath):
        """
        Saves the YAML to a file

        Parameters
        ----------
        filepath : str
            Path where the YAML file will be stored - it should end with
            .yaml
        """
        with open(filepath, "w") as file:
            yaml.dump(self.processing_steps, file, sort_keys=True)


class NoOperationDataAuditLog(DataAuditLogBase):
    """
    A no operation version of the data audit log. This is used when no
    DataAuditLog instance is passed into the functions. This allows
    users to process with logging steps (although this is not
    recommended)
    """

    def add_step(self):
        pass

    def convert_to_json(self):
        pass


def key_steps_log(*log_args):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # Access the audit_log from the 'self' argument
            audit_log = getattr(self, "audit_log", None)
            if audit_log is not None:
                log_info = {arg: kwargs.get(arg) for arg in log_args}
                audit_log.add_step(func.__name__, log_info)
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


# class DataProcessor:
#     def __init__(self, audit_log=None):
#         self.audit_log = audit_log if audit_log else NoOperationDataAuditLog()

#     @key_steps_log("style", "a1")
#     def theta_calc(self, style="first", N0=2000, a1=2.5):
#         # logic
#         pass

#     @key_steps_log("type", "window")
#     def smooth_neutrons(type="SG", window=12):
#         # logic
#         pass


# audit_log = DataAuditLog()

# processor = DataProcessor(audit_log=audit_log)
# processor.theta_calc(style="second", a1=3.5)
# processor.smooth_neutrons(type="SG", window=12)

# audit_log.save_to_yaml("test.yaml")

# output = audit_log.convert_to_yaml()
