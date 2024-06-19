import pandas as pd

from neptoon.corrections_and_functions.neutrons_to_soil_moisture import (
    convert_neutrons_to_soil_moisture,
)
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
        self._water_equiv_of_soil_organic_matter = self._convert_som_to_wsom(
            soil_organic_matter
        )
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
    def water_equiv_of_soil_organic_matter(self):
        return self._water_equiv_of_soil_organic_matter

    @property
    def corrected_neutrons_col_name(self):
        return self._corrected_neutrons_col_name

    def _validate_crns_data_frame(self):
        """
        TODO: Internal method to validate the dataframe can be used:
            - Column Names
            - Attributes correctly given etc.
        """
        pass

    def calculate_sm_estimates(
        self, soil_moisture_column_name: str = "soil_moisture_crns"
    ):
        """
        Calculates soil moisture and adds a column to the dataframe with
        the soil moisture estimate.

        TODO: when we implement kholi method this could be divided into
        internal routines, and then a user can select which method to
        apply.
        """
        self.crns_data_frame[soil_moisture_column_name] = (
            self.crns_data_frame.apply(
                lambda row: convert_neutrons_to_soil_moisture(
                    dry_soil_bulk_density=self.dry_soil_bulk_density,
                    neutron_count=row[self.corrected_neutrons_col_name],
                    n0=self.n0,
                    lattice_water=self.lattice_water,
                    water_equiv_soil_organic_carbon=self.water_equiv_of_soil_organic_matter,
                ),
                axis=1,
            )
        )
        pass

    def calculate_uncertainty_of_sm_estimates(self):
        """
        TODO: produce the uncertainty
        """
        pass

    def calculate_depth_of_measurement(self):
        """
        TODO Adds D86 column
        """
        pass

    def calculate_horizontal_footprint(self):
        """
        TODO Adds horizontal footprint column
        """
        pass

    def _convert_som_to_wsom(self):
        """
        TODO: Convert soil organic matter to water equivelant
        """
        pass

    def process_data(self):
        """
        TODO: Overall process method which will chain together the other
        methods to produce a fully developed DataFrame.
        """
        self.calculate_sm_estimates()
        self.calculate_depth_of_measurement()
        self.calculate_horizontal_footprint()
        self.calculate_uncertainty_of_sm_estimates()

    def return_data_frame(self):
        """
        Returns the crns DataFrame

        Returns
        -------
        pd.DataFrame
            The stored DataFrame
        """
        return self.crns_data_frame
