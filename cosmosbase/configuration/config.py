import os
import logging
from platformdirs import PlatformDirs
import yaml


class ConfigurationObject:
    """
    Base object for storing YAML configuration values. The object is
    initialised with dictionary which could be nested.
    """

    def __init__(self, dictionary):
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


class LoadConfigurationFile:
    """
    Default configuration class.
    """

    def __init__(self, file_path):
        self._file_path = file_path
        self._whole_yaml_file = {}

    @property
    def file_path(self):
        return self._file_path

    @file_path.setter
    def file_path(self, value):
        self._file_path = value

    @property
    def whole_yaml_file(self):
        return self._whole_yaml_file

    @whole_yaml_file.setter
    def whole_yaml_file(self, value):
        self._whole_yaml_file = value

    def save_configuration(self, new_path):
        """TODO"""
        pass

    def _import_whole_yaml_file(self):
        """
        Load the yaml file

        Returns
        -------
        dict
            Dictionary containing the yaml file contents
        """
        with open(self.file_path, "r") as file:
            yaml_file = yaml.safe_load(file)
        self.whole_yaml_file = yaml_file

    def load_configuration(self):
        self._import_whole_yaml_file()
        return ConfigurationObject(self.whole_yaml_file)


class ConfigurationManager:
    def __init__(self):
        self._configs = {}

    def load_configuration(self, name, file_path):
        loader = LoadConfigurationFile(file_path)
        self._configs[name] = loader.load_configuration()

    def get_configuration(self, name):
        return self._configs.get(name)


class GlobalConfig:
    """Configuration values that are not to be updated by the user.
    Should only be updated by developers when required
    """

    _dirs = PlatformDirs("cosmosbase", "CRNS")

    @staticmethod
    def get_cache_dir():
        return GlobalConfig._dirs.user_cache_dir

    @staticmethod
    def create_cache_dir():
        directory = GlobalConfig.get_cache_dir()
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                logging.info(f"Directory created: {directory}")
            except OSError as error:
                logging.error(f"Error creating directory: {error}")
                raise


class TestYamlConfig:
    def __init__(self, config):
        self.config = config
        self.value = 1
        self.station = 2
