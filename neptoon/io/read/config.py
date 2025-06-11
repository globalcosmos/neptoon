from pathlib import Path
import pandas as pd
from typing import Literal

from neptoon.io.read.data_ingest import (
    FileCollectionConfig,
    ManageFileCollection,
    ParseFilesIntoDataFrame,
    InputDataFrameFormattingConfig,
    FormatDataForCRNSDataHub,
    validate_and_convert_file_path,
)
from neptoon.config.configuration_input import ConfigurationManager, BaseConfig
from neptoon.logging import get_logger

core_logger = get_logger()


def _get_config_section(
    configuration_object: ConfigurationManager,
    wanted_config: Literal["sensor", "process"],
):
    """
    Retrieves the specific config from the configuration manager.

    Parameters
    ----------
    configuration_object : ConfigurationManager
        The configuration object containing loaded configs
    wanted_object : Literal["sensor", "process"]
        The type of configuration object to retrieve

    Returns
    -------
    Optional[BaseConfig]
        The requested configuration object if found, None otherwise
    """
    try:
        return configuration_object.get_config(name=wanted_config)
    except (AttributeError, KeyError):
        core_logger.info(f"Configuration for {wanted_config} not found.")
        return None


def _return_config(
    path_to_config,
    config_to_return: Literal["sensor", "process"],
):
    """
    Loads the config file into a ConfigurationManager and returns the
    sensor config part

    Parameters
    ----------
    path_to_config : str | Path
        Path to config file (in yaml format)
    config_to_return: Literal["sensor", "process"]
        name of config to return
    """
    configuration_object = ConfigurationManager()
    configuration_object.load_configuration(
        file_path=path_to_config,
    )
    return _get_config_section(
        configuration_object=configuration_object,
        wanted_config=config_to_return,
    )


def _return_config(
    path_to_config,
    config_to_return: Literal["sensor", "process"],
):
    """
    Loads the config file into a ConfigurationManager and returns the
    sensor config part

    Parameters
    ----------
    path_to_config : str | Path
        Path to config file (in yaml format)
    config_to_return: Literal["sensor", "process"]
        name of config to return
    """
    configuration_object = ConfigurationManager()
    configuration_object.load_configuration(
        file_path=path_to_config,
    )
    return _get_config_section(
        configuration_object=configuration_object,
        wanted_config=config_to_return,
    )


class DataHubFromConfig:
    """
    Creates a DataHub instance using a configuration file.

    This class handles the configuration and initialization of a
    CRNSDataHub using a sensor configuration file. It manages raw data
    parsing, time series preparation, and final hub creation.

    Example:
    --------
    >>> # Method 1: Using a path to sensor configuration file
    >>> sensor_config_path = "/path/to/configurations/A101_station.yaml"
    >>> data_hub_creator = DataHubFromConfig(path_to_sensor_config=sensor_config_path)
    >>> data_hub = data_hub_creator.create_data_hub()
    >>>
    >>> # Method 2: Using a pre-configured ConfigurationManager
    >>> config_manager = ConfigurationManager()
    >>> config_manager.load_configuration(file_path=sensor_config_path)
    >>> data_hub_creator = DataHubFromConfig(configuration_object=config_manager)
    >>> data_hub = data_hub_creator.create_data_hub()
    >>>
    >>> # After creating the data hub, you can proceed with operations:
    >>> data_hub.attach_nmdb_data(station="JUNG")
    >>> data_hub.prepare_static_values()
    """

    def __init__(
        self,
        path_to_sensor_config: str | Path = None,
        configuration_object: ConfigurationManager = None,
        sensor_config: BaseConfig = None,  # Internal use
    ):
        """

        Parameters
        ----------
        path_to_sensor_config : str | Path, optional
            path where sensor config file is found , by default None
        configuration_object : ConfigurationManager, optional
            ConfigurationManager, presumed to contain a sensor config
            object, by default None
        sensor_config : BaseConfig, optional
            SensorConfig directly supplied (internal use with
            ProcessWithConfig), by default None
        """
        self.configuration_object = None
        self.sensor_config = None

        path_to_sensor_config = validate_and_convert_file_path(
            path_to_sensor_config
        )
        self.sensor_config = self._initialise_configuration(
            path_to_sensor_config=path_to_sensor_config,
            configuration_object=configuration_object,
            sensor_config=sensor_config,
        )

    def _initialise_configuration(
        self,
        path_to_sensor_config: str | Path,
        configuration_object: ConfigurationManager,
        sensor_config: BaseConfig,
    ):
        """
        Organises the initialisation steps to ensure a configuration
        object is available

        Parameters
        ----------
        path_to_sensor_config : str | Path, optional
            path where sensor config file is found , by default None
        configuration_object : ConfigurationManager, optional
            ConfigurationManager, presumed to contain a sensor config
            object, by default None
        sensor_config : BaseConfig, optional
            SensorConfig directly supplied (internal use with
            ProcessWithConfig), by default None

        Returns
        -------
        sensor_config
            sensor config file
        """
        if sensor_config is not None:
            return sensor_config
        elif configuration_object:
            sensor_config = _get_config_section(
                configuration_object=self.configuration_object,
                wanted_config="sensor",
            )
            return sensor_config
        elif path_to_sensor_config:
            sensor_config = _return_config(
                path_to_config=path_to_sensor_config, config_to_return="sensor"
            )
            return sensor_config
        else:
            self._no_data_given_error()

    def _no_data_given_error(self):
        """
        Raise ValueError if nothing supplied

        Raises
        ------
        ValueError
            No Data
        """
        message = (
            "Please provide either a path_to_sensor_config"
            " or a configuration_object"
        )
        core_logger.error(message)
        raise ValueError(message)

    def _parse_raw_data(
        self,
    ):
        """
        Parses raw data files.

        Returns
        -------
        pd.DataFrame
            DataFrame from raw files.
        """
        # create tmp object for more readable code
        tmp = self.sensor_config.raw_data_parse_options

        file_collection_config = FileCollectionConfig(
            data_location=tmp.data_location,
            column_names=tmp.column_names,
            prefix=tmp.prefix,
            suffix=tmp.suffix,
            encoding=tmp.encoding,
            skip_lines=tmp.skip_lines,
            separator=tmp.separator,
            decimal=tmp.decimal,
            skip_initial_space=tmp.skip_initial_space,
            parser_kw_strip_left=tmp.parser_kw.strip_left,
            parser_kw_digit_first=tmp.parser_kw.digit_first,
            starts_with=tmp.starts_with,
            multi_header=tmp.multi_header,
            strip_names=tmp.strip_names,
            remove_prefix=tmp.remove_prefix,
        )
        file_manager = ManageFileCollection(config=file_collection_config)
        file_manager.get_list_of_files()
        file_manager.filter_files()
        file_parser = ParseFilesIntoDataFrame(
            file_manager=file_manager, config=file_collection_config
        )
        parsed_data = file_parser.make_dataframe()

        return parsed_data

    def _import_data(
        self,
    ):
        """
        Imports data using information in the config file. If raw data
        requires parsing it will do this. If not, it is presumed the
        data is already available in a single csv file. It then uses the
        supplied information in the YAML files to prepare this for use
        in neptoon.

        Returns
        -------
        pd.DataFrame
            Prepared DataFrame
        """
        if self.sensor_config.raw_data_parse_options.parse_raw_data:
            raw_data_parsed = self._parse_raw_data()
        else:
            raw_data_parsed = pd.read_csv(
                validate_and_convert_file_path(
                    file_path=self.sensor_config.time_series_data.path_to_data,
                )
            )
        df = self._prepare_time_series(raw_data_parsed=raw_data_parsed)
        return df

    def _prepare_time_series(
        self,
        raw_data_parsed: pd.DataFrame,
    ):
        """
        Method for preparing the time series data.

        Returns
        -------
        pd.DataFrame
            Returns a formatted dataframe
        """
        input_formatter_config = InputDataFrameFormattingConfig()
        input_formatter_config.config_info = self.sensor_config
        input_formatter_config.build_from_config()

        data_formatter = FormatDataForCRNSDataHub(
            data_frame=raw_data_parsed,
            config=input_formatter_config,
        )
        df = data_formatter.format_data_and_return_data_frame()
        return df

    def create_data_hub(self):
        """
        Creates a CRNSDataHub using the supplied configuration
        information.

        This method processes raw data according to the configuration
        settings, formats it appropriately, and initializes a new
        CRNSDataHub instance.

        Returns
        -------
        CRNSDataHub
            A fully configured CRNSDataHub instance ready for further
            processing
        """
        # import here to avoid circular dependency
        from neptoon.hub import CRNSDataHub

        return CRNSDataHub(
            crns_data_frame=self._import_data(),
            sensor_info=self.sensor_config.sensor_info,
        )
