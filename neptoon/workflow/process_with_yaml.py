import pandas as pd
from typing import Literal, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
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
from neptoon.quality_control.saqc_methods_and_params import YamlRegistry
from neptoon.quality_control import QualityCheck
from neptoon.corrections import (
    CorrectionType,
    CorrectionTheory,
)
from neptoon.calibration import CalibrationConfiguration
from neptoon.quality_control.saqc_methods_and_params import QAMethod
from neptoon.columns import ColumnInfo
from neptoon.config.configuration_input import ConfigurationManager

core_logger = get_logger()


class ProcessWithYaml:

    def __init__(
        self,
        configuration_object: ConfigurationManager,
        # run_with_data_audit_log: bool = True,
    ):
        self.configuration_object = configuration_object
        # self.run_with_data_audit_log = run_with_data_audit_log
        self.process_config = self._get_config_object(wanted_object="process")
        self.sensor_config = self._get_config_object(wanted_object="sensor")
        self.data_hub = None

    def _get_config_object(
        self,
        wanted_object: Literal["sensor", "processing"],
    ):
        """
        Collects the specific config object from the larger
        configuration object.

        Parameters
        ----------
        wanted_object : Literal["sensor", "processing"]
            The object to collect

        Returns
        -------
        ConfigurationObject
            The required configuration object.
        """
        return self.configuration_object.get_config(name=wanted_object)

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

        self.raw_data_parsed = parsed_data

    def _prepare_time_series(
        self,
    ):
        """
        Method for preparing the time series data.

        Returns
        -------
        pd.DataFrame
            Returns a formatted dataframe
        """
        self.input_formatter_config = InputDataFrameFormattingConfig()
        self.input_formatter_config.yaml_information = self.sensor_config
        self.input_formatter_config.build_from_yaml()
        # date_time_column = self.input_formatter_config.

        data_formatter = FormatDataForCRNSDataHub(
            data_frame=self.raw_data_parsed,
            config=self.input_formatter_config,
        )
        df = data_formatter.format_data_and_return_data_frame()
        return df

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
            self._parse_raw_data()
        else:
            self.raw_data_parsed = pd.read_csv(
                validate_and_convert_file_path(
                    file_path=self.sensor_config.time_series_data.path_to_data,
                )
            )
        df = self._prepare_time_series()
        return df

    def _attach_nmdb_data(
        self,
    ):
        """
        Attaches incoming neutron data with NMDB database.
        """
        tmp = self.process_config.correction_steps.incoming_radiation
        self.data_hub.attach_nmdb_data(
            station=tmp.reference_neutron_monitor.station,
            reference_value=tmp.reference_value,
            new_column_name=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
            resolution=tmp.reference_neutron_monitor.resolution,
            nmdb_table=tmp.reference_neutron_monitor.nmdb_table,
        )

    def _prepare_static_values(
        self,
    ):
        """
        Prepares the SiteInformation values by converting them into
        column in the data frame.

        Currently it just uses method in the CRNSDataHub.
        """
        self.data_hub.prepare_static_values()

    def _apply_quality_assessment(
        self,
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
        self.data_hub.add_quality_flags(add_check=list_of_checks)
        self.data_hub.apply_quality_flags()

    def _prepare_quality_assessment(
        self,
        partial_config,
        name_of_target: str = None,
    ):
        """


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

        qa_builder = QualityAssessmentWithYaml(
            partial_config=partial_config,
            sensor_config=self.sensor_config,
            name_of_target=name_of_target,
        )
        list_of_checks = qa_builder.create_checks()
        return list_of_checks

    def _select_corrections(
        self,
    ):
        """
        Selects corrections.

        See CorrectionSelectorWithYaml
        """
        selector = CorrectionSelectorWithYaml(
            data_hub=self.data_hub,
            process_config=self.process_config,
            sensor_config=self.sensor_config,
        )
        self.data_hub = selector.select_corrections()

    def _correct_neutrons(self):
        """
        Runs the correction routine.
        """
        self.data_hub.correct_neutrons()

    def _produce_soil_moisture_estimates(self):
        """
        Completes the soil moisture estimation step
        """
        self.data_hub.produce_soil_moisture_estimates()

    def _save_data(
        self,
    ):
        """
        Arranges saving the data in the folder.
        """
        file_name = self.sensor_config.sensor_info.name
        try:
            initial_folder_str = self.sensor_config.data_storage.save_folder
        except AttributeError:
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
        append_yaml_bool = bool(
            self.sensor_config.data_storage.append_yaml_hash_to_folder_name
        )
        self.data_hub.save_data(
            folder_name=file_name,
            save_folder_location=folder,
            append_yaml_hash_to_folder_name=append_yaml_bool,
        )

    def _calibrate_data(
        self,
    ):
        """Calibrates the sensor when this is selected."""
        calib_df_path = validate_and_convert_file_path(
            file_path=self.sensor_config.calibration.location
        )
        calib_df = pd.read_csv(calib_df_path)
        self.data_hub.calibration_samples_data = calib_df
        calibration_config = CalibrationConfiguration(
            date_time_column_name=self.sensor_config.calibration.key_column_names.date_time,
            profile_id_column=self.sensor_config.calibration.key_column_names.profile_id,
            distance_column=self.sensor_config.calibration.key_column_names.radial_distance_from_sensor,
            sample_depth_column=self.sensor_config.calibration.key_column_names.sample_depth,
            soil_moisture_gravimetric_column=self.sensor_config.calibration.key_column_names.gravimetric_soil_moisture,
            bulk_density_of_sample_column=self.sensor_config.calibration.key_column_names.bulk_density_of_sample,
            soil_organic_carbon_column=self.sensor_config.calibration.key_column_names.soil_organic_carbon,
            lattice_water_column=self.sensor_config.calibration.key_column_names.lattice_water,
        )
        self.data_hub.calibrate_station(config=calibration_config)
        self.sensor_config.sensor_info.N0 = self.data_hub.sensor_info.N0
        self.data_hub.crns_data_frame["N0"] = self.sensor_config.sensor_info.N0

    def create_data_hub(
        self,
        return_data_hub: bool = True,
    ):
        """
        Creates a CRNSDataHub using the supplied information from the
        YAML config file.

        By default this method will return a configured CRNSDataHub.

        When running the whole process with the run() method, it will
        save the data hub to an attribute so that it can access it for
        further steps.

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

        if return_data_hub:
            return CRNSDataHub(
                crns_data_frame=self._import_data(),
                sensor_info=self.sensor_config.sensor_info,
            )
        else:
            self.data_hub = CRNSDataHub(
                crns_data_frame=self._import_data(),
                sensor_info=self.sensor_config.sensor_info,
            )

    def run_full_process(
        self,
    ):
        """
        Full process run with YAML file

        Raises
        ------
        ValueError
            When no N0 supplied and no calibration completed.
        """
        self.create_data_hub(return_data_hub=False)
        self._attach_nmdb_data()
        self._prepare_static_values()
        # QA raw N spikes
        self._apply_quality_assessment(
            partial_config=self.process_config.neutron_quality_assessment,
            name_of_target="raw_neutrons",
        )
        # QA meteo
        self._apply_quality_assessment(
            partial_config=self.sensor_config.input_data_qa,
            name_of_target=None,
        )

        self._select_corrections()
        self._correct_neutrons()

        if self.sensor_config.calibration.calibrate:
            self._calibrate_data()

        if self.sensor_config.sensor_info.N0 is None:
            message = (
                "Cannot proceed with quality assessment or processing "
                "without an N0 number. Supply an N0 number in the YAML "
                "file or use site calibration"
            )
            core_logger.error(message)
            raise ValueError(message)

        self._apply_quality_assessment(
            partial_config=self.process_config.neutron_quality_assessment,
            name_of_target="corrected_neutrons",
        )
        self._produce_soil_moisture_estimates()
        # self._make_figures()
        self._save_data()


class QualityAssessmentWithYaml:
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
                target = YamlRegistry.get_target(name_of_target)
                method = YamlRegistry.get_method(check_method)
                if method in [QAMethod.ABOVE_N0, QAMethod.BELOW_N0_FACTOR]:
                    check_params["N0"] = self.sensor_config.sensor_info.N0
                check = QualityCheck(
                    target=target, method=method, parameters=check_params
                )
                self.checks.append(check)


class CorrectionSelectorWithYaml:
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

    def _pressure_correction(self):
        """
        Assigns the chosen pressure correction method.

        Raises
        ------
        ValueError
            Unknown correction method
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

    def _humidity_correction(self):
        """
        Assigns the chosen humidity correction method.

        Raises
        ------
        ValueError
            Unknown correction method
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

    def _incoming_intensity_correction(self):
        """
        Assigns the chosen incoming intensity correction method.

        Raises
        ------
        ValueError
            Unknown correction method
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
