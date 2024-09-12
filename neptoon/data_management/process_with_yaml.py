import pandas as pd
from typing import Literal

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
from neptoon.data_management.column_information import ColumnInfo
from neptoon.configuration.configuration_input import ConfigurationManager


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
        self.create_data_hub(return_data_hub=False)
        self._attach_nmdb_data()
        self._prepare_static_values()

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

    def _prepare_quality_assessment(
        self,
    ):
        pass

    def _apply_quality_assessment():
        pass

    def _select_corrections(
        self,
    ):
        pass

    def _correct_neutrons():
        pass

    def _produce_soil_moisture_estimates():
        pass

    def _save_data():
        pass
