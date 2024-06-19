import pandas as pd

from neptoon.logging import get_logger


core_logger = get_logger()


class NeutronsToSM:

    def __init__(
        self,
        crns_data_frame: pd.DataFrame,
        n0: float,
        dry_soil_bulk_density: float = 0,
        lattice_water: float = 0,
        soil_organic_matter: float = 0,
        corrected_neutrons_col_name: str = "epithermal_neutrons_corrected",
    ):
        self._crns_data_frame = crns_data_frame
        self._n0 = n0
        self._dry_soil_bulk_density = dry_soil_bulk_density
        self._lattice_water = lattice_water
        self._soil_organic_matter = soil_organic_matter
        self._corrected_neutrons_col_name = corrected_neutrons_col_name

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_data_frame(self, df):
        # TODO add checks
        self._crns_data_frame = df

    @property
    def n0(self):
        return self._n0

    @property
    def dry_soil_bulk_density(self):
        return self._dry_soil_bulk_density

    @property
    def lattice_water(self):
        return self._lattice_water

    @property
    def soil_organic_matter(self):
        return self._soil_organice_matter

    @property
    def corrected_neutrons_col_name(self):
        return self._corrected_neutrons_col_name

    def _validate_crns_data_frame(self):
        """
        TODO Internal method to validate the dataframe can be used:
            - Column Names
            - Attributes correctly given etc.
        """
        pass

    def calculate_sm_estimates(self):
        pass

    def _convert_som_to_wsom(self):
        pass
