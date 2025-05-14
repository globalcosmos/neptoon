import pandas as pd
from typing import Literal

from neptoon.columns import ColumnInfo
from neptoon.corrections import convert_neutrons_to_soil_moisture, Schroen2017
from neptoon.logging import get_logger
from neptoon.data_audit import log_key_step

core_logger = get_logger()


class NeutronsToSM:
    """
    Class for converting a DataFrame containing corrected neutrons into
    soil moisture estimates. Includes calculations for depth.
    """

    def __init__(
        self,
        crns_data_frame: pd.DataFrame,
        n0: float,
        dry_soil_bulk_density: float = 1.4,
        lattice_water: float = 0,
        soil_organic_carbon: float = 0,
        corrected_neutrons_col_name: str = str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT
        ),
        smoothed_neutrons_col_name: str = str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ),
        soil_moisture_col_name: str = str(ColumnInfo.Name.SOIL_MOISTURE),
        depth_column_name: str = str(
            ColumnInfo.Name.SOIL_MOISTURE_MEASURMENT_DEPTH
        ),
        conversion_theory: Literal[
            "desilets_2010", "koehli_2021"
        ] = "desilets_2010",
    ):
        """
        Attributes to be added to the class.

        Parameters
        ----------
        crns_data_frame : pd.DataFrame
            _description_
        n0 : float
            The n0 term
        dry_soil_bulk_density : float, optional
            in g/cm3, by default 1.4
        lattice_water : float, optional
            in decimal percent, by default 0
        soil_organic_carbon : float, optional
            in decimal percent, by default 0
        corrected_neutrons_col_name : str, optional
            column name where corrected neutrons are to be found, by
            default str( ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT )
        smoothed_neutrons_col_name : str, optional
            column name where smoothed corrected neutron counts are
            found , by default str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL )
        soil_moisture_col_name : str, optional
            column name where soil moisture should be written, by
            default str(ColumnInfo.Name.SOIL_MOISTURE)
        depth_column_name : str, optional
            column name where depth estimates are written, by default str(
            ColumnInfo.Name.SOIL_MOISTURE_MEASURMENT_DEPTH )
        """
        self._crns_data_frame = crns_data_frame
        self.n0 = n0
        self.dry_soil_bulk_density = (
            dry_soil_bulk_density
            if dry_soil_bulk_density is not None
            else 1.42
        )
        self.lattice_water = lattice_water if lattice_water is not None else 0
        self.soil_organic_carbon = (
            soil_organic_carbon if soil_organic_carbon is not None else 0
        )
        self.water_equiv_of_soil_organic_matter = self._convert_soc_to_wsom(
            self._soil_organic_carbon
        )
        self.corrected_neutrons_col_name = corrected_neutrons_col_name
        self.smoothed_neutrons_col_name = smoothed_neutrons_col_name
        self.soil_moisture_col_name = soil_moisture_col_name
        self.depth_column_name = depth_column_name

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_data_frame(self, df):
        # TODO add checks
        self._crns_data_frame = df

    def _validate_crns_data_frame(self):
        """
        TODO: Internal method to validate the dataframe can be used:
            - Column Names
            - Attributes correctly given etc.
        """
        pass

    @staticmethod
    def _convert_soc_to_wsom(soc):
        """
        Converts soil organic carbon values into water equivelant soil
        organic matter.

        doi: https://doi.org/10.1002/2013WR015138

        """
        return soc * 0.556

    def calculate_sm_estimates(
        self,
        neutron_data_column_name: str,
        soil_moisture_column_write_name: str,
    ):
        """
        Calculates soil moisture estimates and adds them to the
        dataframe.

        This method applies the neutron-to-soil-moisture conversion for
        each row in the dataframe and stores the results in a new
        column.

        Parameters
        ----------
        neutron_data_column_name : str
            The name of the column containing neutron count data.
        soil_moisture_column_write_name : str
            The name of the new column to store calculated soil moisture
            values.

        Returns
        -------
        None
            The method modifies the dataframe in-place.

        Notes
        -----
        This method assumes that the neutron data has been properly
        corrected and that all necessary parameters (n0, bulk density,
        etc.) have been set.
        """

        self.crns_data_frame[soil_moisture_column_write_name] = (
            self.crns_data_frame.apply(
                lambda row: convert_neutrons_to_soil_moisture(
                    dry_soil_bulk_density=self.dry_soil_bulk_density,
                    neutron_count=row[neutron_data_column_name],
                    n0=self.n0,
                    lattice_water=self.lattice_water,
                    water_equiv_soil_organic_matter=self.water_equiv_of_soil_organic_matter,
                ),
                axis=1,
            )
        )

    def calculate_uncertainty_of_sm_estimates(self):
        """
        TODO: produce the uncertainty
        """
        self.calculate_sm_estimates(
            neutron_data_column_name=str(
                ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_LOWER_COUNT
            ),
            soil_moisture_column_write_name=str(
                ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_UPPER
            ),
        )
        self.calculate_sm_estimates(
            neutron_data_column_name=str(
                ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UPPER_COUNT
            ),
            soil_moisture_column_write_name=str(
                ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_LOWER
            ),
        )

    @log_key_step("radius")
    def calculate_depth_of_measurement(
        self,
        radius: float = 50,
    ):
        """
        Creates a column with the calculated depth of measurement

        TODO: what radius to set as standard?

        Parameters
        ----------
        radius : float, optional
            The default radius of measurement (avg), by default 50
        """
        self.crns_data_frame[self.depth_column_name] = (
            self.crns_data_frame.apply(
                lambda row: Schroen2017.calculate_measurement_depth(
                    distance=radius,
                    bulk_density=self.dry_soil_bulk_density,
                    soil_moisture=row[self.soil_moisture_col_name],
                ),
                axis=1,
            )
        )

    def calculate_horizontal_footprint(self):
        """
        TODO Adds horizontal footprint column
        """
        pass

    def calculate_all_soil_moisture_data(self):
        """
        TODO: Overall process method which will chain together the other
        methods to produce a fully developed DataFrame.
        """

        self.calculate_sm_estimates(
            neutron_data_column_name=str(
                ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
            ),
            soil_moisture_column_write_name=str(ColumnInfo.Name.SOIL_MOISTURE),
        )
        self.calculate_uncertainty_of_sm_estimates()
        self.calculate_depth_of_measurement()
        self.calculate_horizontal_footprint()  # TODO

    def return_data_frame(self):
        """
        Returns the crns DataFrame

        Returns
        -------
        pd.DataFrame
            The stored DataFrame
        """
        return self.crns_data_frame
