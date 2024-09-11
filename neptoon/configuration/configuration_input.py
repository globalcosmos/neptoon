import logging
import yaml
from typing import Literal
from abc import ABC, abstractmethod
from neptoon.logging import get_logger
from neptoon.configuration.yaml_classes import (
    GeneralSiteMetadata,
    CRNSSensorInformation,
    TimeseriesDataFormat,
    CalibrationDataFormat,
    CalibrationDataFormat_ColumnNames,
    PDFConfiguration,
    DataStorage,
    MethodSignifier,
    IncomingRadiation,
    AirPressure,
    AirHumidity,
    InvalidData,
    Interpolation,
    TemporalAggregation,
)

core_logger = get_logger()


class ConfigurationObject:
    """
    Base object for storing YAML configuration values. The object is
    initialised with dictionary which could be nested. It will
    recursively add attributes in a nested fasion.
    """

    def __init__(self, dictionary: dict):
        """
        Initialises the object.

        Parameters
        ----------
        dictionary : dict
            Takes a nested dictionary and sets the values into a
            nested object.
        """
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigurationObject(value))
            elif isinstance(value, list):
                setattr(
                    self,
                    key,
                    [
                        (
                            ConfigurationObject(item)
                            if isinstance(item, dict)
                            else item
                        )
                        for item in value
                    ],
                )
            else:
                setattr(self, key, value)

    def to_dict(self):
        """
        Converts the ConfigurationObject and its nested attributes
        back into a dictionary.

        This is mainly used for testing.

        Returns
        -------
        dict
            Dictionary representation of the object
        """
        output_dict = {}
        for key, value in self.__dict__.items():
            if isinstance(value, ConfigurationObject):
                output_dict[key] = value.to_dict()
            elif isinstance(value, list):
                output_list = []
                for item in value:
                    if isinstance(item, ConfigurationObject):
                        output_list.append(item.to_dict())
                    else:
                        output_list.append(item)
                output_dict[key] = output_list
            else:
                output_dict[key] = value
        return output_dict


class PreLoadConfigurationYaml:
    """
    This class handles loading of the yaml file and stores it as an
    attribute.
    """

    def __init__(self):
        self._whole_yaml_file = {}

    @property
    def whole_yaml_file(self):
        return self._whole_yaml_file

    @whole_yaml_file.setter
    def whole_yaml_file(self, value):
        self._whole_yaml_file = value

    def import_whole_yaml_file(self, file_path: str):
        """
        Load the yaml file

        Returns
        -------
        dict
            Dictionary containing the yaml file contents
        """
        with open(file_path, "r") as file:
            yaml_file = yaml.safe_load(file)
        self.whole_yaml_file = yaml_file


class ValidateConfigurationFile(ABC):
    """
    Base class for configuration file validation. Defines the structure
    and required methods for validating different sections of a
    configuration file.

    This class should not be instantiated directly but extended by
    specific configuration validation classes.

    """

    def __init__(self, config_yaml: PreLoadConfigurationYaml):
        """Initialise the validation class.

        Parameters
        ----------
        config_yaml : PreLoadConfigurationYaml
            An instance of the preloadconfigurationyaml class.
        """
        self._config_yaml = config_yaml

    @property
    def config_yaml(self):
        return self._config_yaml

    @config_yaml.setter
    def config_yaml(self, value):
        self._config_yaml = value

    @staticmethod
    def remove_nested_dicts(some_dict: dict):
        """Return a new dictionary with nested dictionaries removed.

        Parameters
        ----------
        some_dict : dict
            A dictionary

        Returns
        -------
        dict
            A dictionary but without any nested dictionaries in it
        """
        return {k: v for k, v in some_dict.items() if not isinstance(v, dict)}

    @abstractmethod
    def get_sections(self):
        """
        Collects the sections of the YAML.

        Implemented individually for each configuration type

        """
        pass

    @abstractmethod
    def check_sections(self):
        """
        Validates the collected sections of the YAML.

        Implemented individually for each configuration type.

        """
        pass

    def validate_configuration(self):
        """
        Enacts both the section extraction as well as the validation of
        the sections against the pydantic tables.
        """
        self.get_sections()
        self.check_sections()


class SensorConfigurationValidation(ValidateConfigurationFile):
    """
    Validates sensor configuration YAML. Implements the abstract methods
    defined in ValidateConfigurationFile to provide validation logic for
    sensor configurations.

    See ValidateConfigurationFile for more details on the methods.
    """

    def get_sections(self):
        """
        Extracts the individual sections from the YAML file and stores
        them as attributes in the object instance.

        TODO: return to this when built!!!
        """
        pass
        # full_yaml = self.config_yaml.whole_yaml_file

        # self.general_site_metadata = full_yaml.get("general_site_metadata", {})
        # self.timeseries_data_format = full_yaml.get("time_series_data", {})

        # self.timeseries_data_format_columns = self.timeseries_data_format[
        #     "key_column_info"
        # ]
        # self.timeseries_data_format = self.remove_nested_dicts(
        #     self.timeseries_data_format
        # )

        # self.calibration_data_format = full_yaml.get(
        #     "calibration_data_format", {}
        # )
        # self.calibration_data_format_key_columns = (
        #     self.calibration_data_format["key_column_names"]
        # )
        # self.calibration_data_format = self.remove_nested_dicts(
        #     self.calibration_data_format
        # )
        # self.crns_sensor_information = full_yaml.get(
        #     "crns_sensor_information", {}
        # )

        # self.pdf_formatting = full_yaml.get("pdf_formatting", {})
        # self.data_storage = full_yaml.get("data_storage", {})

    def check_sections(self):
        """
        Validates the stored sections against pydantic data tables to
        ensure data types are as expected. The models are not saved and
        are only used for validation.

        TODO: return to this when built!!
        """
        pass
        # GeneralSiteMetadata(**self.general_site_metadata)
        # CRNSSensorInformation(**self.crns_sensor_information)
        # TimeseriesDataFormat(**self.timeseries_data_format)
        # CalibrationDataFormat(**self.calibration_data_format)
        # CalibrationDataFormat_ColumnNames(
        #     **self.calibration_data_format_key_columns
        # )
        # PDFConfiguration(**self.pdf_formatting)
        # DataStorage(**self.data_storage)
        # SoilGridsMetadata(**self.)


class ProcessConfigurationValidation(ValidateConfigurationFile):
    def get_sections(self):
        """
        Extracts the individual sections from the YAML file and stores
        them as attributes in the object instance.
        """
        pass
        # full_yaml = self.config_yaml.whole_yaml_file
        # correction_steps = full_yaml.get("correction_steps", {})

        # self.method_signifier = full_yaml.get("method_signifier", {})
        # self.air_humidity = correction_steps.get("air_humidity", {})
        # self.air_pressure = correction_steps.get("air_pressure", {})
        # self.incoming_radiation = correction_steps.get(
        #     "incoming_radiation", {}
        # )
        # self.reference_neutron_monitor = self.incoming_radiation.get(
        #     "reference_neutron_monitor", {}
        # )
        # self.invalid_data = full_yaml.get("invalid_data", {})
        # self.interpolation = full_yaml.get("interpolation", {})
        # self.temporal_aggregation = full_yaml.get("temporal_aggregation", {})

    def check_sections(self):
        """
        Validates the stored sections against pydantic data tables to
        ensure data types are as expected. The models are not saved and
        are only used for validation.

        """
        pass
        # MethodSignifier(**self.method_signifier)
        # AirHumidity(**self.air_humidity)
        # AirPressure(**self.air_pressure)
        # IncomingRadiation(**self.incoming_radiation)
        # InvalidData(**self.invalid_data)
        # Interpolation(**self.interpolation)
        # TemporalAggregation(**self.temporal_aggregation)


class InputDataFrameConfigurationValidation:
    pass


class ConfigurationManager:
    """
    Configuration Management class. The purpose of this class is to
    store multiple configuration objects in one location.

    The configuration objects are read in from YAML files and validated
    against pydantic tables to ensure types are as expected. If no type
    errors are presented it will then recursively import the YAML file
    using the ConfigurationObject class. This means that values can be
    read in that are not validated at all, for example if some
    additional data is included but is not necessarily important for the
    code to run.

    Possible configuration input types are: [station, processing,
    global].

    """

    def __init__(self):
        self._configs = {}

    def convert_configuration_dictionary(self, dictionary: dict):
        """Convert the YAML dict into a ConfigurationObject

        Returns
        -------
        Class
            Configuration object with attributes
        """

        configuration_object = ConfigurationObject(dictionary)

        return configuration_object

    def load_and_validate_configuration(
        self,
        name: Literal[
            "station",
            "processing",
            "global",
            "input_data",
        ],
        file_path: str,
    ):
        """
        This class handles loading and validating of YAML configuration
        files. The output is a ConfigurationObject that has been type
        checked

        Parameters
        ----------
        name : str
            configuration type name

            Can be only either:
            - sensor
            - processing
            - global
            - input_data

        file_path : str
            File path of the configuration YAML file

        Raises
        ------
        NameError
            Error when incompatable name is given
        """
        pre_load = PreLoadConfigurationYaml()
        pre_load.import_whole_yaml_file(file_path)

        name_lower = name.lower()
        if name_lower == "station":
            validation_object = SensorConfigurationValidation(pre_load)
            validation_object.validate_configuration()
        elif name_lower == "processing":
            validation_object = ProcessConfigurationValidation(pre_load)
            validation_object.validate_configuration()
        elif name_lower == "global":
            pass
            # validation_object = GlobalSettingsConfigurationValidataion(
            #     pre_load
            # )
            # validation_object.validate_configuration()
        elif name_lower == "input_data":
            pass
            # validation_object = InputDataFrameConfigurationValidation(pre_load)
            # validation_object.validate_configuration()

        else:
            core_logger.error(
                "Incompatible name given when configuration file loaded."
            )
            raise NameError(
                f"{name} is not an accepted name for configuration file "
                f"type. Accepted names are [station, processing]"
            )

        self._configs[name] = self.convert_configuration_dictionary(
            pre_load.whole_yaml_file
        )

    def get_configuration(
        self,
        name: Literal[
            "station",
            "processing",
            "global",
            "input_data",
        ],
    ):
        """
        Get the configuration file

        Parameters
        ----------
        name : str
            Name of the configuration object. Can be either [sensor,
            processing, global]

        Returns
        -------
        ConfigurationObject
            ConfigurationObject of the specified name
        """
        return self._configs.get(name)
