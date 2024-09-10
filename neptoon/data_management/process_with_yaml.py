import pandas as pd

from neptoon.data_management.crns_data_hub import CRNSDataHub


class ProcessWithYaml:

    def __init__(
        self,
        configuration_object,
        pre_configure_corrections=False,
    ):
        self.configuration_object = configuration_object

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
