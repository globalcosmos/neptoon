import pandas as pd

from neptoon.data_management.crns_data_hub import CRNSDataHub
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
        self.configuration_object.get_configuration(wanted_object)

    def create_data_hub():
        pass

    def process_site():
        pass

    def _collect_data():
        pass

    def _create_site_information():
        pass

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
