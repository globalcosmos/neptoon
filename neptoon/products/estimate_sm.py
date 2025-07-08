import pandas as pd
from typing import Literal, Optional
import pandera
import pandera.pandas as pa

###
from neptoon.columns import ColumnInfo
from neptoon.corrections import (
    neutrons_to_total_grav_soil_moisture_desilets_etal_2010,
    neutrons_to_total_grav_soil_moisture_koehli_etal_2021,
    Schroen2017,
)
from neptoon.data_prep.conversions import AbsoluteHumidityCreator
from neptoon.logging import get_logger
from neptoon.data_audit import log_key_step
from neptoon.quality_control.utils import _validate_df

core_logger = get_logger()

###
# Pandera schema for validation
###

base_input_schema = pa.DataFrameSchema(
    {
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UPPER_COUNT
        ): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_LOWER_COUNT
        ): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
    },
    index=pa.Index(dtype=pd.DatetimeTZDtype(unit="ns", tz="UTC"), coerce=True),
    strict=False,
)

input_schema_koehli = pa.DataFrameSchema(
    {
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UPPER_COUNT
        ): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_LOWER_COUNT
        ): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(ColumnInfo.Name.ABSOLUTE_HUMIDITY): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
    },
    index=pa.Index(dtype=pd.DatetimeTZDtype(unit="ns", tz="UTC"), coerce=True),
    strict=False,
)

output_schema = pa.DataFrameSchema(
    {
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UPPER_COUNT
        ): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_LOWER_COUNT
        ): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_VOL_UPPER): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_VOL_LOWER): pa.Column(
            dtype=float,
            coerce=True,
            nullable=True,
        ),
        str(ColumnInfo.Name.SOIL_MOISTURE_MEASUREMENT_RADIUS): pa.Column(
            float,
            coerce=True,
            nullable=True,
        ),
        str(ColumnInfo.Name.SOIL_MOISTURE_MEASURMENT_DEPTH): pa.Column(
            float,
            coerce=True,
            nullable=True,
        ),
        str(ColumnInfo.Name.SOIL_MOISTURE_VOL): pa.Column(
            float,
            coerce=True,
            nullable=True,
        ),
        str(ColumnInfo.Name.SOIL_MOISTURE_GRAV): pa.Column(
            float,
            coerce=True,
            nullable=True,
        ),
    },
    index=pa.Index(dtype=pd.DatetimeTZDtype(unit="ns", tz="UTC"), coerce=True),
    strict=False,
)


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
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ),
        soil_moisture_vol_col_name: str = str(
            ColumnInfo.Name.SOIL_MOISTURE_VOL
        ),
        soil_moisture_grav_col_name: str = str(
            ColumnInfo.Name.SOIL_MOISTURE_GRAV
        ),
        depth_column_name: str = str(
            ColumnInfo.Name.SOIL_MOISTURE_MEASURMENT_DEPTH
        ),
        radius_column_name: str = str(
            ColumnInfo.Name.SOIL_MOISTURE_MEASUREMENT_RADIUS
        ),
        conversion_theory: Literal[
            "desilets_etal_2010", "koehli_etal_2021"
        ] = "desilets_etal_2010",
        koehli_method_form: Literal[
            "Jan23_uranos",
            "Jan23_mcnpfull",
            "Mar12_atmprof",
            "Mar21_mcnp_drf",
            "Mar21_mcnp_ewin",
            "Mar21_uranos_drf",
            "Mar21_uranos_ewin",
            "Mar22_mcnp_drf_Jan",
            "Mar22_mcnp_ewin_gd",
            "Mar22_uranos_drf_gd",
            "Mar22_uranos_ewin_chi2",
            "Mar22_uranos_drf_h200m",
            "Aug08_mcnp_drf",
            "Aug08_mcnp_ewin",
            "Aug12_uranos_drf",
            "Aug12_uranos_ewin",
            "Aug13_uranos_atmprof",
            "Aug13_uranos_atmprof2",
        ] = "Mar21_uranos_drf",
        abs_air_humidity_col_name=str(ColumnInfo.Name.ABSOLUTE_HUMIDITY),
        air_pressure_col_name=str(ColumnInfo.Name.AIR_PRESSURE),
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
            default str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL )
        soil_moisture_vol_col_name : str, optional
            column name where volumetric soil moisture should be
            written, by default str(ColumnInfo.Name.SOIL_MOISTURE)
        depth_column_name : str, optional
            column name where depth estimates are written, by default
            str( ColumnInfo.Name.SOIL_MOISTURE_MEASURMENT_DEPTH )
        radius_column_name : str, optional
            column name where radius estimates are written, by default
            str( ColumnInfo.Name.SOIL_MOISTURE_MEASUREMENT_RADIUS )
        """
        self._crns_data_frame = _validate_df(
            crns_data_frame, schema=base_input_schema
        )
        self.n0 = n0
        # None vals can be passed from CRNSDataHub so leave these if else statements
        self.dry_soil_bulk_density = (
            dry_soil_bulk_density
            if dry_soil_bulk_density is not None
            else 1.42
        )
        self.lattice_water = lattice_water if lattice_water is not None else 0
        self.soil_organic_carbon = (
            soil_organic_carbon if soil_organic_carbon is not None else 0
        )
        self.water_equiv_soil_organic_carbon = self._convert_soc_to_wsom(
            self.soil_organic_carbon
        )
        self.corrected_neutrons_col_name = corrected_neutrons_col_name
        self.soil_moisture_grav_col_name = soil_moisture_grav_col_name
        self.soil_moisture_vol_col_name = soil_moisture_vol_col_name
        self.depth_column_name = depth_column_name
        self.radius_column_name = radius_column_name
        self.conversion_theory = conversion_theory
        self.koehli_method_form = koehli_method_form
        self.abs_air_humidity_col_name = abs_air_humidity_col_name
        self.air_pressure_col_name = air_pressure_col_name
        self.air_humidity_uncorrected = False

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_data_frame(self, df):
        self._crns_data_frame = df

    @staticmethod
    def _convert_soc_to_wsom(soc):
        """
        Converts soil organic carbon values into water equivelant soil
        organic matter.

        doi: https://doi.org/10.1002/2013WR015138

        """
        return soc * 0.556

    def _check_if_humidity_correction_applied(
        self,
        auto_uncorrect=True,
    ):
        """
        Checks if corrected neutrons have already been corrected for
        humidity. If they have it, and auto_uncorrect is True, it will
        uncorrect them. The UTS function corrects for humidity in the
        conversion to soil moisture.

        Parameters
        ----------
        auto_uncorrect : bool, optional
            Whether to dis-apply the humidity correction, by default
            True
        """
        if (
            str(ColumnInfo.Name.HUMIDITY_CORRECTION)
            in self.crns_data_frame.columns
        ) and not self.air_humidity_uncorrected:
            if auto_uncorrect:
                self.crns_data_frame[
                    str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)
                ] = (
                    self.crns_data_frame[
                        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)
                    ]
                    / self.crns_data_frame[
                        str(ColumnInfo.Name.HUMIDITY_CORRECTION)
                    ]
                )
                self.air_humidity_uncorrected = True
                message = (
                    "Using köhli 2021 UTS method, but humidity correctio already applied.\n"
                    "Humidity correction was removed from corrected counts."
                )
                print(message)
                core_logger.info(message)

    def _ensure_abs_humidity_available(self):
        """
        Ensures that absolute himidity data is available for processing
        using Koehli et al., 2021.
        """
        abs_hum_creator = AbsoluteHumidityCreator(self.crns_data_frame)
        self.crns_data_frame = (
            abs_hum_creator.check_and_return_abs_hum_column()
        )

    def calculate_sm_estimates(
        self,
        neutron_data_column_name: str,
        soil_moisture_column_write_name_grav: Optional[str] = None,
        soil_moisture_column_write_name_vol: Optional[str] = None,
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
        soil_moisture_column_write_name_grav : str
            The name of the new column to store calculated gravimetric
            soil moisture values.
        soil_moisture_column_write_name_vol : str
            The name of the new column to store calculated volumetric
            soil moisture values.

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
        # Create a series of grav soil moisture (incl. LW and WESOC)
        if self.conversion_theory == "desilets_etal_2010":
            raw_grav = self.crns_data_frame.apply(
                lambda row: neutrons_to_total_grav_soil_moisture_desilets_etal_2010(
                    neutrons=row[neutron_data_column_name],
                    n0=self.n0,
                ),
                axis=1,
            )

        elif self.conversion_theory == "koehli_etal_2021":
            print(
                "Using Koehli et al., 2021 method for converting neutrons to soil moisture"
            )
            print("This takes a little longer... please stand by....")

            self._check_if_humidity_correction_applied(auto_uncorrect=True)
            self._ensure_abs_humidity_available()

            self.crns_data_frame = _validate_df(
                self.crns_data_frame, schema=input_schema_koehli
            )
            raw_grav = self.crns_data_frame.apply(
                lambda row: neutrons_to_total_grav_soil_moisture_koehli_etal_2021(
                    neutron_count=row[neutron_data_column_name],
                    n0=self.n0,
                    lattice_water=self.lattice_water,
                    abs_air_humidity=row[self.abs_air_humidity_col_name],
                    water_equiv_soil_organic_carbon=self.water_equiv_soil_organic_carbon,
                    koehli_method_form=self.koehli_method_form,
                ),
                axis=1,
            )

        grav_sm = (
            raw_grav
            - self.lattice_water
            - self.water_equiv_soil_organic_carbon
        )

        if soil_moisture_column_write_name_grav:
            self.crns_data_frame[soil_moisture_column_write_name_grav] = (
                grav_sm
            )

        if soil_moisture_column_write_name_vol:
            self.crns_data_frame[soil_moisture_column_write_name_vol] = (
                grav_sm * self.dry_soil_bulk_density
            )

    def _from_grav_to_vol_sm(self, grav_sm, bulk_density):
        """
        Converts gravimetric to volumetric soil moisture

        Parameters
        ----------
        grav_sm : float
            Gravimetric soil moisture
        bulk_density : float
            Bulk density

        Returns
        -------
        float
            Volumetric Soil moisture
        """

        return grav_sm * bulk_density

    def calculate_uncertainty_of_sm_estimates(self):
        """
        Produces uncertainty estimates of soil mositure.
        """
        self.calculate_sm_estimates(
            neutron_data_column_name=str(
                ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_LOWER_COUNT
            ),
            soil_moisture_column_write_name_vol=str(
                ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_VOL_UPPER
            ),
        )
        self.calculate_sm_estimates(
            neutron_data_column_name=str(
                ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UPPER_COUNT
            ),
            soil_moisture_column_write_name_vol=str(
                ColumnInfo.Name.SOIL_MOISTURE_UNCERTAINTY_VOL_LOWER
            ),
        )

    @log_key_step("radius")
    def calculate_depth_of_measurement(
        self,
        radius: float = 50,
    ):
        """
        Creates a column with the calculated depth of measurement (cm)

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
                    volumetric_soil_moisture=row[
                        self.soil_moisture_vol_col_name
                    ],
                ),
                axis=1,
            )
        )

    def calculate_horizontal_footprint(self):
        """
        Creates a column with the calculated radius of measurement (m).
        """

        self.crns_data_frame[self.radius_column_name] = (
            self.crns_data_frame.apply(
                lambda row: Schroen2017.calculate_footprint_radius(
                    volumetric_soil_moisture=row[
                        self.soil_moisture_vol_col_name
                    ],
                    abs_air_humidity=row[self.abs_air_humidity_col_name],
                    atmospheric_pressure=row[self.air_pressure_col_name],
                ),
                axis=1,
            )
        )

    def calculate_all_soil_moisture_data(self):
        """
        TODO: Overall process method which will chain together the other
        methods to produce a fully developed DataFrame.
        """

        self.calculate_sm_estimates(
            neutron_data_column_name=self.corrected_neutrons_col_name,
            soil_moisture_column_write_name_grav=self.soil_moisture_grav_col_name,
            soil_moisture_column_write_name_vol=self.soil_moisture_vol_col_name,
        )
        self.calculate_uncertainty_of_sm_estimates()
        self.calculate_depth_of_measurement()
        self.calculate_horizontal_footprint()
        self.crns_data_frame = _validate_df(
            df=self.crns_data_frame, schema=output_schema
        )

    def return_data_frame(self):
        """
        Returns the crns DataFrame

        Returns
        -------
        pd.DataFrame
            The stored DataFrame
        """
        return self.crns_data_frame
