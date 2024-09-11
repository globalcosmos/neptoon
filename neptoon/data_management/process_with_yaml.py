import pandas as pd

from neptoon.data_management.crns_data_hub import CRNSDataHub
from neptoon.data_management.site_information import SiteInformation
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

    def _get_config_object(
        self,
        wanted_object: str,
    ):
        return self.configuration_object.get_configuration(name=wanted_object)

    def create_data_hub(self):
        pass

    def process_site():
        pass

    def _collect_data():
        pass

    def _create_site_information(self):
        """
        Creates a SiteInformation object using the station_info
        configuration object.

        Returns
        -------
        SiteInformation
            The complete SiteInformation object.
        """
        site_info = SiteInformation(
            latitude=(self.station_info.general_site_metadata.latitude),
            longitude=(self.station_info.general_site_metadata.longitude),
            elevation=(self.station_info.general_site_metadata.elevation),
            reference_incoming_neutron_value=(
                self.station_info.general_site_metadata.reference_incoming_neutron_value
            ),
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

    def _attach_nmdb_data():
        pass

    def _prepare_static_values():
        pass

    def _prepare_quality_assessment():
        pass

    def _apply_quality_assessment():
        pass

    def _select_corrections():
        pass

    def _correct_neutrons():
        pass

    def _produce_soil_moisture_estimates():
        pass

    def _save_data():
        pass
