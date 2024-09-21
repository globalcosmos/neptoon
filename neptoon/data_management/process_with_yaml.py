import pandas as pd
from typing import Literal
from pathlib import Path
from neptoon.logging import get_logger
from neptoon.data_management.crns_data_hub import CRNSDataHub
from neptoon.data_management.site_information import SiteInformation
from neptoon.data_ingest_and_formatting.data_ingest import (
    FileCollectionConfig,
    ManageFileCollection,
    ParseFilesIntoDataFrame,
    InputDataFrameFormattingConfig,
    FormatDataForCRNSDataHub,
    validate_and_convert_file_path,
)
from neptoon.quality_assesment.quality_assesment import (
    FlagSpikeDetectionUniLOF,
    FlagNeutronGreaterThanN0,
    FlagBelowMinimumPercentN0,
)
from neptoon.neutron_correction.neutron_correction import (
    CorrectionType,
    CorrectionTheory,
)
from neptoon.data_management.column_information import ColumnInfo
from neptoon.configuration.configuration_input import ConfigurationManager

core_logger = get_logger()


class ProcessWithYaml:

    def __init__(
        self,
        configuration_object: ConfigurationManager,
        pre_configure_corrections=False,
    ):
        self.configuration_object = configuration_object
        self.process_info = self._get_config_object(wanted_object="processing")
        self.station_info = self._get_config_object(wanted_object="station")
        self.data_hub = None

    def _get_config_object(
        self,
        wanted_object: Literal["station", "processing"],
    ):
        """
        Collects the specific config object from the larger
        configuration object.

        Parameters
        ----------
        wanted_object : Literal["station", "processing"]
            The object to collect

        Returns
        -------
        ConfigurationObject
            The required configuration object.
        """
        return self.configuration_object.get_configuration(name=wanted_object)

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

        if return_data_hub:
            return CRNSDataHub(
                crns_data_frame=self._import_data(),
                site_information=self._create_site_information(),
            )
        else:
            self.data_hub = CRNSDataHub(
                crns_data_frame=self._import_data(),
                site_information=self._create_site_information(),
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
            name_of_section="flag_raw_neutrons",
            partial_config=(
                self.process_info.neutron_quality_assessment.flag_raw_neutrons
            ),
        )
        # QA meteo
        # TODO

        self._select_corrections()
        self._correct_neutrons()

        # OPTIONAL: Calibration
        # TODO

        if self.station_info.general_site_metadata.N0 is None:
            message = (
                "Cannot proceed with quality assessment or processing "
                "without an N0 number. Supply an N0 number in the YAML "
                "file or complete site calibration"
            )
            core_logger.error(message)
            raise ValueError(message)

        self._apply_quality_assessment(
            name_of_section="flag_corrected_neutrons",
            partial_config=(
                self.process_info.neutron_quality_assessment.flag_raw_neutrons
            ),
        )
        self._produce_soil_moisture_estimates()
        self._save_data()

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
        tmp = self.station_info.raw_data_parse_options

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
            parser_kw=tmp.parser_kw.to_dict(),
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
        self.input_formatter_config.yaml_information = self.station_info
        self.input_formatter_config.build_from_yaml()

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
        if self.station_info.raw_data_parse_options.parse_raw_data:
            self._parse_raw_data()
        else:
            self.raw_data_parsed = pd.to_csv(
                validate_and_convert_file_path(
                    file_path=self.station_info.time_series_data.path_to_data,
                )
            )
        df = self._prepare_time_series()
        return df

    def _create_site_information(
        self,
    ):
        """
        Creates a SiteInformation object using the station_info
        configuration object.

        Returns
        -------
        SiteInformation
            The complete SiteInformation object.
        """
        tmp = self.station_info.general_site_metadata

        site_info = SiteInformation(
            site_name=tmp.site_name,
            latitude=tmp.latitude,
            longitude=tmp.longitude,
            elevation=tmp.elevation,
            reference_incoming_neutron_value=tmp.reference_incoming_neutron_value,
            dry_soil_bulk_density=(
                self.station_info.general_site_metadata.avg_dry_soil_bulk_density
            ),
            lattice_water=(
                self.station_info.general_site_metadata.avg_lattice_water
            ),
            soil_organic_carbon=(
                self.station_info.general_site_metadata.avg_soil_organic_carbon
            ),
            cutoff_rigidity=(
                self.station_info.general_site_metadata.cutoff_rigidity
            ),
            mean_pressure=(
                self.station_info.general_site_metadata.mean_pressure
            ),
            site_biomass=(self.station_info.general_site_metadata.avg_biomass),
            n0=(self.station_info.general_site_metadata.N0),
            beta_coefficient=(
                self.station_info.general_site_metadata.beta_coefficient
            ),
            l_coefficient=(
                self.station_info.general_site_metadata.l_coefficient
            ),
        )
        return site_info

    def _attach_nmdb_data(
        self,
    ):
        """
        Attaches incoming neutron data with NMDB database.
        """
        tmp = (
            self.process_info.correction_steps.incoming_radiation.reference_neutron_monitor
        )
        self.data_hub.attach_nmdb_data(
            station=tmp.station,
            new_column_name=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
            resolution=tmp.resolution,
            nmdb_table=tmp.nmdb_table,
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
        name_of_section: str,
        partial_config,
    ):
        """
        Method to create quality flags

        Parameters
        ----------
        name_of_section : str
            Name of the section of the partial_config
        partial_config : ConfigurationObject
            A ConfigurationObject section

        Notes
        -----

        The name_of_section should match the final part of the supplied
        partial_config. For example:

        partial_config = (
            config.process_info.neutron_quality_assessment.flag_raw_neutrons
            )

        Therefore:

        name_of_section = 'flag_raw_neutrons'

        """
        list_of_checks = self._prepare_quality_assessment(
            name_of_section=name_of_section,
            partial_config=partial_config,
        )
        self.data_hub.add_quality_flags(add_check=list_of_checks)
        self.data_hub.apply_quality_flags()

    def _prepare_quality_assessment(
        self,
        name_of_section: str,
        partial_config,
    ):
        """


        Parameters
        ----------
        name_of_section : str
            Name of the section of the partial_config
        partial_config : ConfigurationObject
            A ConfigurationObject section

        Notes
        -----

        See _apply_quality_assessment() above.

        Returns
        -------
        List
            List of QualityChecks
        """

        qa_builder = QualityAssessmentWithYaml(
            name_of_section=name_of_section,
            partial_config=partial_config,
            station_info=self.station_info,
        )
        list_of_checks = qa_builder.collect_and_return_checks()
        return list_of_checks

    def _select_corrections(
        self,
    ):
        """
        See CorrectionSelectorWithYaml!!!!
        """
        selector = CorrectionSelectorWithYaml(
            data_hub=self.data_hub,
            process_info=self.process_info,
            station_info=self.station_info,
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

        file_name = self.station_info.general_site_metadata.site_name
        initial_folder_str = self.station_info.data_storage.save_folder
        folder = (
            Path.cwd()
            if initial_folder_str is None
            else Path(initial_folder_str)
        )

        append_yaml_bool = bool(
            self.station_info.data_storage.append_yaml_to_folder_name
        )
        print(file_name)
        print(folder)

        self.data_hub.save_data(
            folder_name=file_name,
            save_folder_location=folder,
            append_yaml_hash_to_folder_name=append_yaml_bool,
        )


class QualityAssessmentWithYaml:
    """
    Handles bulding out QualityChecks from config files.
    """

    def __init__(
        self,
        name_of_section: str,
        partial_config,
        station_info,
    ):
        """
        Attributes.

        Parameters
        ----------
        name_of_section : str
            The name of the section that has been supplied. See Notes.
        partial_config : ConfigurationObject
            A selection from the ConfigurationObject.
        station_info : ConfigurationObject
            The config object describing station variables

        Notes
        -----

        The name_of_section should match the final part of the supplied
        partial_config. For example:

        partial_config = (
            config.process_info.neutron_quality_assessment.flag_raw_neutrons
            )

        Means:

        name_of_section = 'flag_raw_neutrons'
        """
        self.name_of_section = name_of_section
        self.partial_config = partial_config
        self.station_info = station_info
        self.checks = []

    def collect_and_return_checks(
        self,
    ):
        """
        Base function which chooses correct internal method to use
        depending on the supplied config section.

        Returns
        -------
        List[QualityCheck]
            A list of QualityChecks
        """
        if self.name_of_section == "flag_raw_neutrons":
            self._flag_raw_neutrons()
        elif self.name_of_section == "extra_quality_assessment":
            pass  # TODO
        elif self.name_of_section == "flag_corrected_neutrons":
            self._flag_corrected_neutrons()

        return self.checks

    def _flag_raw_neutrons(self):
        """
        Process to prepare flags for raw neutron values.
        """
        obj_as_dict = vars(self.partial_config)
        for key, value in obj_as_dict.items():
            if key == "spikes":
                self._process_spikes(value)

    def _process_spikes(self, config) -> None:
        """
        Helper method to process spike configuration.
        """

        col_name = (
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)
            if config.col_name == "default"
            else config.col_name
        )

        if config.method.lower() == "unilof":
            self.checks.append(
                FlagSpikeDetectionUniLOF(
                    column_name=col_name,
                    periods_in_calculation=config.periods_in_calculation,
                    threshold=config.threshold,
                )
            )
        else:
            message = f"Unsupported spike detection method: {config.method}"
            core_logger.error(message)

    def _flag_corrected_neutrons(self):
        """
        Process to prepare flags for corrected neutron values.
        """
        obj_as_dict = vars(self.partial_config)
        for key, value in obj_as_dict.items():
            if key == "greater_than_N0":
                self._process_greater_than_N0(value)
            elif key == "below_N0_factor":
                self._process_below_N0_factor(value)

    def _process_greater_than_N0(self, config):
        """
        Helper method to process greater_than_N0 configuration.
        """
        col_name = (
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)
            if config.col_name == "default"
            else config.col_name
        )

        self.checks.append(
            FlagNeutronGreaterThanN0(
                N0=self.station_info.general_site_metadata.N0,
                neutron_col_name=col_name,
                above_N0_factor=config.above_N0_factor,
            )
        )

    def _process_below_N0_factor(self, config):
        """
        Helper method to process below_N0_factor configuration.
        """
        col_name = (
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)
            if config.col_name == "default"
            else config.col_name
        )

        self.checks.append(
            FlagBelowMinimumPercentN0(
                N0=self.station_info.general_site_metadata.N0,
                neutron_col_name=col_name,
                percent_minimum=config.not_below,
            )
        )


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
        data_hub: CRNSDataHub,
        process_info,
        station_info,
    ):
        """
        Attributes

        Parameters
        ----------
        data_hub : CRNSDataHub
            A CRNSDataHub hub instance
        process_info :
            The process YAML as an object.
        station_info :
            The station information YAML as an object
        """
        self.data_hub = data_hub
        self.process_info = process_info
        self.station_info = station_info

    def _pressure_correction(self):
        """
        Assigns the chosen pressure correction method.

        Raises
        ------
        ValueError
            Unknown correction method
        """
        tmp = self.process_info.correction_steps.air_pressure

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
        tmp = self.process_info.correction_steps.air_humidity

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
        tmp = self.process_info.correction_steps.incoming_radiation

        if tmp.method.lower() == "hawdon_2014":
            self.data_hub.select_correction(
                correction_type=CorrectionType.INCOMING_INTENSITY,
                correction_theory=CorrectionTheory.HAWDON_2014,
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
        TODO
        """
        pass

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
