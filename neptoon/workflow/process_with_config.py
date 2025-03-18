import pandas as pd
from typing import Literal, TYPE_CHECKING
from pathlib import Path

# if TYPE_CHECKING:
from neptoon.hub import CRNSDataHub

from neptoon.logging import get_logger
from neptoon.io.read.data_ingest import (
    FileCollectionConfig,
    ManageFileCollection,
    ParseFilesIntoDataFrame,
    InputDataFrameFormattingConfig,
    FormatDataForCRNSDataHub,
    validate_and_convert_file_path,
)
from neptoon.io.save.save_data import ConfigSaver
from neptoon.quality_control.saqc_methods_and_params import QAConfigRegistry
from neptoon.quality_control import QualityCheck
from neptoon.corrections import (
    CorrectionType,
    CorrectionTheory,
)
from neptoon.calibration import CalibrationConfiguration
from neptoon.quality_control.saqc_methods_and_params import QAMethod
from neptoon.columns import ColumnInfo
from neptoon.config.configuration_input import ConfigurationManager, BaseConfig
from magazine import Magazine

core_logger = get_logger()


def _get_config_section(
    configuration_object: ConfigurationManager,
    wanted_config: Literal["sensor", "processing"],
):
    """
    Retrieves the specific config object from the configuration manager.

    Parameters
    ----------
    wanted_object : Literal["sensor", "processing"]
        The type of configuration object to retrieve

    Returns
    -------
    Optional[ConfigurationObject]
        The required configuration object if found, None otherwise
    """
    try:
        return configuration_object.get_config(name=wanted_config)
    except (AttributeError, KeyError):
        core_logger.info(f"Configuration for {wanted_config} not found.")
        return None


def _return_config(
    self, path_to_config, config_to_return: Literal["sensor", "processing"]
):
    """
    Loads the config file into a ConfigurationManager and returns
    the sensor config part

    Parameters
    ----------
    path_to_sensor_config : str | Path
        Path to sensor config file
    """
    configuration_object = ConfigurationManager()
    configuration_object.load_configuration(
        file_path=path_to_config,
    )
    self.configuration_object = configuration_object
    return _get_config_section(
        self.configuration_object, wanted_config=config_to_return
    )


def _no_data_given_error():
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


class DataHubFromConfig:
    """
    Creates a DataHub instance using a configuration file.
    """

    def __init__(
        self,
        path_to_sensor_config: str | Path = None,
        configuration_object: ConfigurationManager = None,
        sensor_config: BaseConfig = None,  # Internal use
    ):
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
        Organises the preprocessing steps to ensure a configuration
        object is available
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
            _no_data_given_error()

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
        Creates a CRNSDataHub using the supplied information from the
        config file.

        Parameters
        ----------
        return_data_frame : bool, optional
            Whether to return the CRNSDataHub directly, by default True

        Returns
        -------
        CRNSDataHub
            The CRNSDataHub
        """
        # import here to avoid circular dependency
        from neptoon.hub import CRNSDataHub

        return CRNSDataHub(
            crns_data_frame=self._import_data(),
            sensor_info=self.sensor_config.sensor_info,
        )


class ProcessWithConfig:
    """Process data using config files."""

    def __init__(
        self,
        path_to_sensor_config: str | Path = None,
        path_to_process_config: str | Path = None,
        configuration_object: ConfigurationManager = None,
    ):
        # Initialise blank attributes
        self.configuration_object = None
        self.sensor_config = None
        self.process_config = None
        self.data_hub = None

        # Set up base attributes
        self.sensor_config, self.process_config = (
            self._initialise_configuration(
                path_to_sensor_config=path_to_sensor_config,
                path_to_process_config=path_to_process_config,
                configuration_object=configuration_object,
            )
        )

    def _initialise_configuration(
        self,
        path_to_sensor_config: str | Path,
        path_to_process_config: str | Path,
        configuration_object: ConfigurationManager,
    ):
        """
        Creates the sensor and process config files depending on how
        they've been supplied. This could be a directly provided
        ConfigurationManager object or by providing paths to the config
        files

        Parameters
        ----------
        path_to_sensor_config : str | Path
            path to the sensor config file
        path_to_process_config : str | Path
            path to the processing config file
        configuration_object : ConfigurationManager
            a configuration object

        Returns
        -------
        sensor_config, process_config

        """
        if configuration_object:
            sensor_config = configuration_object.get_config("sensor")
            process_config = configuration_object.get_config("process")
            return sensor_config, process_config
        elif path_to_process_config and path_to_sensor_config:
            sensor_config = _return_config(
                path_to_config=path_to_sensor_config,
                config_to_return="sensor",
            )
            process_config = _return_config(
                path_to_config=path_to_process_config,
                config_to_return="processing",
            )
            return sensor_config, process_config
        else:
            _no_data_given_error()

    def _create_data_hub(self, sensor_config: BaseConfig):
        # Import data as data_hub
        data_hub_creator = DataHubFromConfig(sensor_config=sensor_config)
        return data_hub_creator.create_data_hub()

    def _attach_nmdb_data(
        self,
        data_hub: CRNSDataHub,
    ):
        """
        Attaches incoming neutron data with NMDB database.
        """
        tmp = self.process_config.correction_steps.incoming_radiation
        data_hub.attach_nmdb_data(
            station=tmp.reference_neutron_monitor.station,
            new_column_name=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
            resolution=tmp.reference_neutron_monitor.resolution,
            nmdb_table=tmp.reference_neutron_monitor.nmdb_table,
        )
        return data_hub

    def _prepare_static_values(
        self,
        data_hub: CRNSDataHub,
    ):
        """
        Prepares the SiteInformation values by converting them into
        column in the data frame.

        Currently it just uses method in the CRNSDataHub.
        """
        data_hub.prepare_static_values()
        return data_hub

    def _apply_quality_assessment(
        self,
        data_hub: CRNSDataHub,
        partial_config,
        name_of_target: str = None,
    ):
        """
        Method to create quality flags

        Parameters
        ----------
        partial_config : ConfigurationObject
            A ConfigurationObject section
        name_of_target : str
            Name of the target for QA - if None it will loop through
            available targets in the partial_config
        """
        list_of_checks = self._prepare_quality_assessment(
            name_of_target=name_of_target,
            partial_config=partial_config,
        )
        data_hub.add_quality_flags(add_check=list_of_checks)
        data_hub.apply_quality_flags()
        return data_hub

    def _prepare_quality_assessment(
        self,
        partial_config,
        name_of_target: str = None,
    ):
        """
        Prepares quality assessment checks based on configuration.

        Parameters
        ----------

        partial_config : ConfigurationObject
            A ConfigurationObject section
        name_of_target : str
            Name of the target for QA - if None it will loop through
            available targets in the partial_config

        Notes
        -----

        See _apply_quality_assessment() above.

        Returns
        -------
        List
            List of QualityChecks
        """

        qa_builder = QualityAssessmentFromConfig(
            partial_config=partial_config,
            sensor_config=self.sensor_config,
            name_of_target=name_of_target,
        )
        list_of_checks = qa_builder.create_checks()
        return list_of_checks

    def _select_corrections(
        self,
        data_hub: CRNSDataHub,
        process_config: BaseConfig,
        sensor_config: BaseConfig,
    ):
        """
        Selects corrections.

        See CorrectionSelectorFromConfig

        """
        selector = CorrectionSelectorFromConfig(
            data_hub=data_hub,
            process_config=process_config,
            sensor_config=sensor_config,
        )
        data_hub = selector.select_corrections()
        return data_hub

    def _correct_neutrons(
        self,
        data_hub: CRNSDataHub,
    ):
        """
        Runs the correction routine.
        """
        data_hub.correct_neutrons()
        return data_hub

    def _create_neutron_uncertainty_bounds(self, data_hub: CRNSDataHub):
        """
        Creates neutron statistical uncertainty bounds

        Parameters
        ----------
        data_hub : CRNSDataHub
            datahub

        Returns
        -------
        data_hub
            updated data_hub
        """
        data_hub.create_neutron_uncertainty_bounds()
        return data_hub

    def _produce_soil_moisture_estimates(self, data_hub: CRNSDataHub):
        """
        produces soil moisture estimates

        Parameters
        ----------
        data_hub : CRNSDataHub
            datahub

        Returns
        -------
        data_hub
            updated data_hub
        """
        data_hub.produce_soil_moisture_estimates()
        return data_hub

    def _create_figures(
        self,
        data_hub: CRNSDataHub,
        sensor_config: BaseConfig,
    ):
        """
        Creates figures

        Parameters
        ----------
        data_hub : CRNSDataHub
            data_hub

        Return
        ------
        data_hub: CRNSDataHub
            updated data_hub
        """
        if sensor_config.figures.create_figures is False:
            return

        if sensor_config.figures.make_all_figures:
            data_hub.create_figures(create_all=True)
        else:
            to_create_list = [
                name for name in sensor_config.figures.custom_list
            ]
            data_hub.create_figures(
                create_all=False, selected_figures=to_create_list
            )
        return data_hub

    def _config_saver(
        self,
        data_hub: CRNSDataHub,
        sensor_config: BaseConfig,
        process_config: BaseConfig,
    ):
        """
        Saves the config files (with any updates) into the save folder.
        """
        sensor_config_saver = ConfigSaver(
            save_folder_location=data_hub.saver.full_folder_location,
            config=sensor_config,
        )
        sensor_config_saver.save()
        process_config_saver = ConfigSaver(
            save_folder_location=data_hub.saver.full_folder_location,
            config=process_config,
        )
        process_config_saver.save()

    def _save_data(
        self,
        data_hub: CRNSDataHub,
        sensor_config: BaseConfig,
    ):
        """
        Arranges saving the data in the folder.
        """
        file_name = sensor_config.sensor_info.name
        try:
            initial_folder_str = Path(sensor_config.data_storage.save_folder)
        except TypeError:
            initial_folder_str = None
            message = (
                "No data storage location available in config. Using cwd()"
            )
            core_logger.info(message)

        folder = (
            Path.cwd()
            if initial_folder_str is None
            else Path(initial_folder_str)
        )
        append_timestamp_bool = bool(
            sensor_config.data_storage.append_timestamp_to_folder_name
        )
        data_hub.save_data(
            folder_name=file_name,
            save_folder_location=folder,
            append_timestamp=append_timestamp_bool,
        )
        return data_hub

    def _calibrate_data(
        self,
        data_hub: CRNSDataHub,
        sensor_config: BaseConfig,
    ):
        """
        Calibrates the sensor producing an N0 calibration term

        Parameters
        ----------
        data_hub : CRNSDataHub
            DataHub
        sensor_config : BaseConfig
            A sensor config file

        Returns
        -------
        data_hub, sensor_config
            Returns hub with updates from calibration and sensor_config
            with updated N0
        """
        calib_df_path = validate_and_convert_file_path(
            file_path=sensor_config.calibration.location
        )
        calib_df = pd.read_csv(calib_df_path)
        data_hub.calibration_samples_data = calib_df
        calibration_config = CalibrationConfiguration(
            calib_data_date_time_column_name=sensor_config.calibration.key_column_names.date_time,
            calib_data_date_time_format=sensor_config.calibration.date_time_format,
            profile_id_column=sensor_config.calibration.key_column_names.profile_id,
            distance_column=sensor_config.calibration.key_column_names.radial_distance_from_sensor,
            sample_depth_column=sensor_config.calibration.key_column_names.sample_depth,
            soil_moisture_gravimetric_column=sensor_config.calibration.key_column_names.gravimetric_soil_moisture,
            bulk_density_of_sample_column=sensor_config.calibration.key_column_names.bulk_density_of_sample,
            soil_organic_carbon_column=sensor_config.calibration.key_column_names.soil_organic_carbon,
            lattice_water_column=sensor_config.calibration.key_column_names.lattice_water,
        )
        data_hub.calibrate_station(config=calibration_config)
        sensor_config = self._update_sensor_config_after_calibration(
            sensor_config, data_hub
        )
        data_hub = self._update_hub_after_calibration(data_hub=data_hub)
        return data_hub, sensor_config

    def _update_hub_after_calibration(
        self,
        data_hub: CRNSDataHub,
        sensor_config: BaseConfig,
    ):
        """
        Updates the dataframe in the data_hub with a column for N0.

        Parameters
        ----------
        data_hub : CRNSDataHub
            DataHub

        Returns
        -------
        data_hub
            CRNSDataHub
        """

        data_hub = data_hub.crns_data_frame["N0"] = (
            sensor_config.sensor_info.N0
        )
        return data_hub

    def _update_sensor_config_after_calibration(
        self,
        sensor_config,
        data_hub,
    ):
        """
        Updates sensor_config with N0 term calculatd during calibration.

        Parameters
        ----------
        sensor_config : BaseCondig
            The Sensor Config
        data_hub : CRNSDataHub
            DataHub

        Returns
        -------
        sensor_config
            sensor_config file with updated N0
        """
        sensor_config.sensor_info.N0 = data_hub.sensor_info.N0
        return sensor_config

    def _smooth_data(
        self,
        data_hub: CRNSDataHub,
        process_config: BaseConfig,
        column_to_smooth: str,
    ):
        """
        Smooth a data column

        Parameters
        ----------
        data_hub : CRNSDataHub
            Data Hub
        process_config : BaseConfig
            Process Config
        column_to_smooth : str
            name of column to smooth
        """
        smooth_method = process_config.data_smoothing.settings.algorithm
        window = process_config.data_smoothing.settings.window
        poly_order = process_config.data_smoothing.settings.poly_order
        data_hub.smooth_data(
            column_to_smooth=column_to_smooth,
            smooth_method=smooth_method,
            window=window,
            poly_order=poly_order,
        )
        return data_hub

    def _check_n0_available(self, sensor_config: BaseConfig):
        """
        Checks if N0 available before proceeding

        Raises
        ------
        ValueError
            Error if no N0 as cannot work then
        """
        if sensor_config.sensor_info.N0 is None:
            message = (
                "Cannot proceed with quality assessment or processing "
                "without an N0 number. Supply an N0 number in the sensor config "
                "file or use site calibration"
            )
            core_logger.error(message)
            raise ValueError(message)

    def run_full_process(
        self,
    ):
        """
        Full process run with config file

        Raises
        ------
        ValueError
            When no N0 supplied and no calibration completed.
        """
        if self.sensor_config.data_storage.create_report:
            Magazine.active = True

        self.data_hub = self._create_data_hub(sensor_config=self.sensor_config)

        # Prepare data
        self.data_hub = self._attach_nmdb_data(self.data_hub)
        self.data_hub = self._prepare_static_values(self.data_hub)

        # First Quality assessment
        ## Raw Neutrons
        self.data_hub = self._apply_quality_assessment(
            data_hub=self.data_hub,
            partial_config=self.process_config.neutron_quality_assessment,
            name_of_target="raw_neutrons",
        )
        ## Meteo Variables
        self.data_hub = self._apply_quality_assessment(
            data_hub=self.data_hub,
            partial_config=self.sensor_config.input_data_qa,
            name_of_target=None,
        )

        # Corrections
        self.data_hub = self._select_corrections(
            data_hub=self.data_hub,
            process_config=self.process_config,
            sensor_config=self.sensor_config,
        )
        self.data_hub = self._correct_neutrons(self.data_hub)

        # Calibration
        if self.sensor_config.calibration.calibrate:
            self.data_hub, self.sensor_config = self._calibrate_data(
                data_hub=self.data_hub,
                sensor_config=self.sensor_config,
            )

        # Second QA and Smoothing
        self._check_n0_available(sensor_config=self.sensor_config)
        self.data_hub = self._apply_quality_assessment(
            data_hub=self.data_hub,
            partial_config=self.process_config.neutron_quality_assessment,
            name_of_target="corrected_neutrons",
        )
        if self.process_config.data_smoothing.smooth_corrected_neutrons:
            self.data_hub = self._smooth_data(
                data_hub=self.data_hub,
                process_config=self.process_config,
                column_to_smooth=str(
                    ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT
                ),
            )

        # Produce soil moisture estimates
        self.data_hub = self._create_neutron_uncertainty_bounds(self.data_hub)
        self.data_hub = self._produce_soil_moisture_estimates(self.data_hub)
        if self.process_config.data_smoothing.smooth_soil_moisture:
            self.data_hub = self._smooth_data(
                data_hub=self.data_hub,
                process_config=self.process_config,
                column_to_smooth=str(ColumnInfo.Name.SOIL_MOISTURE_FINAL),
            )
        self.data_hub = self._apply_quality_assessment(
            data_hub=self.data_hub,
            partial_config=self.sensor_config.soil_moisture_qa,
            name_of_target=None,
        )

        # Create figures and save outputs
        self.data_hub = self._create_figures(
            data_hub=self.data_hub,
            sensor_config=self.sensor_config,
        )
        self.data_hub = self._save_data(
            data_hub=self.data_hub,
            sensor_config=self.sensor_config,
        )
        self._config_saver(
            data_hub=self.data_hub,
            sensor_config=self.sensor_config,
            process_config=self.process_config,
        )


class QualityAssessmentFromConfig:
    """
    Handles bulding out QualityChecks from config files. When an SaQC
    system is bridged (see quality_assessment.py), for it to be
    accessible for YAML processing it a method must be in here to.

    """

    def __init__(
        self,
        partial_config,
        sensor_config,
        name_of_target: Literal["raw_neutrons", "corrected_neutrons"] = None,
    ):
        """
        Attributes

        Parameters
        ----------

        partial_config : ConfigurationObject
            A selection from the ConfigurationObject which stores QA
            selections
        sensor_config : ConfigurationObject
            The config object describing station variables
        name_of_target : str
            The name of the target for QA. If None it will loop through
            any provided in partial config.

        Notes
        -----

        The name_of_section should match the final part of the supplied
        partial_config. For example:

        partial_config = (
            config.process_config.neutron_quality_assessment.flag_raw_neutrons
            )

        Therefore:

        name_of_section = 'flag_raw_neutrons'
        """

        self.partial_config = partial_config
        self.sensor_config = sensor_config
        self.name_of_target = name_of_target
        self.checks = []

    def create_checks(self):
        """
        Creates the checks based on what is provided in the YAML file.

        Returns
        -------
        List
            A list of Checks is saved in self.checks
        """
        qa_dict = self.partial_config.model_dump()

        # Case 1: Specific target (raw neutrons)
        if self.name_of_target in ["raw_neutrons", "corrected_neutrons"]:
            if self.name_of_target in qa_dict:
                target_dict = qa_dict[self.name_of_target]
                self.return_a_check(
                    name_of_target=self.name_of_target,
                    target_dict=target_dict,
                )

        # Case 2: Process all targets from config
        else:
            for target in qa_dict:
                target_dict = qa_dict.get(target)
                if target_dict:  # Skip if None
                    self.return_a_check(
                        name_of_target=target,
                        target_dict=target_dict,
                    )

        return self.checks

    def return_a_check(self, name_of_target: str, target_dict: dict):
        """
        Process checks for a specific target.
        """
        if not target_dict:  # Guard against None or empty dict
            return

        for check_method, check_params in target_dict.items():
            if isinstance(check_params, dict):
                target = QAConfigRegistry.get_target(name_of_target)
                method = QAConfigRegistry.get_method(check_method)
                if method in [QAMethod.ABOVE_N0, QAMethod.BELOW_N0_FACTOR]:
                    check_params["N0"] = self.sensor_config.sensor_info.N0
                check = QualityCheck(
                    target=target, method=method, parameters=check_params
                )
                self.checks.append(check)


class CorrectionSelectorFromConfig:
    """
    Idea is to work with the Enum objects and Correction Factory based
    on values.

    I'm hoping it will be simply a matter of:

    if processing.pressure == desilets_2012
        factory add - CorrectionType = pressure - CorrectionTheory =
        desilets

    """

    def __init__(
        self,
        data_hub: "CRNSDataHub",
        process_config,
        sensor_config,
    ):
        """
        Attributes

        Parameters
        ----------
        data_hub : CRNSDataHub
            A CRNSDataHub hub instance
        process_config :
            The process YAML as an object.
        sensor_config :
            The station information YAML as an object
        """
        self.data_hub = data_hub
        self.process_config = process_config
        self.sensor_config = sensor_config

    @Magazine.reporting(topic="Neutron Correction")
    def _pressure_correction(self):
        """
        Assigns the chosen pressure correction method.

        Raises
        ------
        ValueError
            Unknown correction method

        Report
        ------
        The pressure correction method used was {tmp.method}.
        """
        tmp = self.process_config.correction_steps.air_pressure
        if tmp.method is None or str(tmp.method).lower() == "none":
            return

        if tmp.method.lower() == "zreda_2012":
            self.data_hub.select_correction(
                correction_type=CorrectionType.PRESSURE,
                correction_theory=CorrectionTheory.ZREDA_2012,
            )
        else:
            message = (
                f"{tmp.method} is not a known pressure correction theory. \n"
                "Please choose another."
            )
            core_logger.error(message)
            raise ValueError(message)

    @Magazine.reporting(topic="Neutron Correction")
    def _humidity_correction(self):
        """
        Assigns the chosen humidity correction method.

        Raises
        ------
        ValueError
            Unknown correction method

        Report
        ------
        The humidity correction was {tmp.method}.
        """
        tmp = self.process_config.correction_steps.air_humidity
        if tmp.method is None or str(tmp.method).lower() == "none":
            return
        if tmp.method.lower() == "rosolem_2013":
            self.data_hub.select_correction(
                correction_type=CorrectionType.HUMIDITY,
                correction_theory=CorrectionTheory.ROSOLEM_2013,
            )
        else:
            message = (
                f"{tmp.method} is not a known humidity correction theory. \n"
                "Please choose another."
            )
            core_logger.error(message)
            raise ValueError(message)

    @Magazine.reporting(topic="Neutron Correction")
    def _incoming_intensity_correction(self):
        """
        Assigns the chosen incoming intensity correction method.

        Raises
        ------
        ValueError
            Unknown correction method

        Report
        ------
        The incoming intensity correction was {tmp.method}.
        """
        tmp = self.process_config.correction_steps.incoming_radiation

        if tmp.method is None or str(tmp.method).lower() == "none":
            return

        if tmp.method.lower() == "hawdon_2014":
            self.data_hub.select_correction(
                correction_type=CorrectionType.INCOMING_INTENSITY,
                correction_theory=CorrectionTheory.HAWDON_2014,
            )
        elif tmp.method.lower() == "zreda_2012:":
            self.data_hub.select_correction(
                correction_type=CorrectionType.INCOMING_INTENSITY,
                correction_theory=CorrectionTheory.ZREDA_2012,
            )
        elif tmp.method.lower() == "mcjannet_desilets_2023:":
            self.data_hub.select_correction(
                correction_type=CorrectionType.INCOMING_INTENSITY,
                correction_theory=CorrectionTheory.MCJANNET_DESILETS_2023,
            )
        else:
            message = (
                f"{tmp.method} is not a known incoming intensity correction theory. \n"
                "Please choose another."
            )
            core_logger.error(message)
            raise ValueError(message)

    def _above_ground_biomass_correction(self):
        """
        Assigns the chosen above ground biomass correction.
        """
        tmp = self.process_config.correction_steps.above_ground_biomass

        if tmp.method is None or str(tmp.method).lower() == "none":
            return

        elif tmp.method.lower() == "baatz_2015":
            self.data_hub.select_correction(
                correction_type=CorrectionType.ABOVE_GROUND_BIOMASS,
                correction_theory=CorrectionTheory.BAATZ_2015,
            )
        elif tmp.method.lower() == "morris_2024:":
            self.data_hub.select_correction(
                correction_type=CorrectionType.ABOVE_GROUND_BIOMASS,
                correction_theory=CorrectionTheory.MORRIS_2024,
            )
        else:
            message = (
                f"{tmp.method} is not a known above ground biomass correction theory. \n"
                "Please choose another."
            )
            core_logger.error(message)
            raise ValueError(message)

    def select_corrections(self):
        """
        Chains together each correction step and outputs the data_hub.

        Returns
        -------
        CRNSDataHub
            With corrections selected.
        """
        self._pressure_correction()
        self._humidity_correction()
        self._incoming_intensity_correction()
        self._above_ground_biomass_correction()

        return self.data_hub
