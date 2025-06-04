import pandas as pd
from enum import Enum
from abc import ABC, abstractmethod
from neptoon.logging import get_logger
from neptoon.columns import ColumnInfo

# read in the specific functions here
from neptoon.corrections import (
    incoming_intensity_correction,
    rc_correction_hawdon,
    McjannetDesilets2023,
    calc_absolute_humidity,
    calc_saturation_vapour_pressure,
    calc_actual_vapour_pressure,
    humidity_correction_rosolem2013,
    calc_pressure_correction_beta_coeff,
    calc_mean_pressure,
    calc_beta_coefficient,
    above_ground_biomass_correction_baatz2015,
    above_ground_biomass_correction_morris2024,
)
from neptoon.data_prep.conversions import AbsoluteHumidityCreator

core_logger = get_logger()


class CorrectionType(Enum):
    """
    The types of correction avaiable to implement.
    """

    INCOMING_INTENSITY = "incoming_intensity"
    ABOVE_GROUND_BIOMASS = "above_ground_biomass"
    PRESSURE = "pressure"
    HUMIDITY = "humidity"
    CUSTOM = "custom"


class CorrectionTheory(Enum):
    """
    The corrections theories for correcting influence on neutron signal
    beyond soil moisture
    """

    # Intensity
    ZREDA_2012 = "zreda_2012"
    HAWDON_2014 = "hawdon_2014"
    MCJANNET_DESILETS_2023 = "mcjannet_desilets_2023"
    # Atmospheric Water Vapour
    ROSOLEM_2013 = "rosolem_2013"
    # Pressure
    # Aboveground Biomass
    BAATZ_2015 = "baatz_2015"
    MORRIS_2024 = "morris_2024"


def is_column_missing_or_empty(data_frame, column_name):
    """
    Find whether a column is missing or empty in a dataframe. Useful for
    checking data before making calculations.

    Parameters
    ----------
    data_frame : pd.DataFrame
        _description_
    column_name : str
        Name of column to check for

    Returns
    -------
    bool
        True or False whether column is missing or empty
    """
    return (
        column_name not in data_frame.columns
        or data_frame[column_name].isnull().all()
    )


class Correction(ABC):
    """
    Abstract class for the Correction classes.

    All corrections have an apply method which takes a DataFrame as an
    argument. The return of the apply function should always be a
    DataFrame with the correction factor calculated and added as a
    column. The correction_factor_column_name should be set to the
    desired column name for the calculated correction factor.

    The CorrectionBuilder class will store the name of columns where
    correction factors are stored (when multiple corrections are
    undertaken). This enables the creation of the overall corrected
    neutron count column.
    """

    def __init__(
        self, correction_type: str, correction_factor_column_name: str
    ):
        self._correction_factor_column_name = correction_factor_column_name
        self.correction_type = correction_type

    @abstractmethod
    def apply(self, data_frame: pd.DataFrame):
        """
        The apply button should always take a dataframe as an input, do
        some logic, and return a dataframe with the additional columns
        calucalted during processing.

        Parameters
        ----------
        data_frame : pd.DataFrame
            The crns_data_frame
        """
        pass

    @property
    def correction_factor_column_name(self) -> str:
        if self._correction_factor_column_name is None:
            raise ValueError("correction_factor_column_name has not been set.")
        return self._correction_factor_column_name

    @correction_factor_column_name.setter
    def correction_factor_column_name(self, value: str):
        self._correction_factor_column_name = value

    def get_correction_factor_column_name(self):
        """
        Declare the name of the correction factor column
        """
        return self.correction_factor_column_name


class IncomingIntensityCorrectionZreda2012(Correction):
    """
    Corrects neutrons for incoming neutron intensity according to the
    original Zreda et al. (2012) equation.

    https://doi.org/10.5194/hess-16-4079-2012
    """

    def __init__(
        self,
        reference_incoming_neutron_value: str = str(
            ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE
        ),
        correction_type: str = CorrectionType.INCOMING_INTENSITY,
        correction_factor_column_name: str = str(
            ColumnInfo.Name.INTENSITY_CORRECTION
        ),
        incoming_neutron_column_name: str = str(
            ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY
        ),
    ):
        """
        Required attributes for creation.

        Parameters
        ----------
        reference_incoming_neutron_value : str
            name of the column holding the reference count of incoming
            neutron intensity at a point in time.
        correction_type : str
            correction type, by default CorrectionType.INCOMING_INTENSITY
        correction_factor_column_name : str, optional
            name of column corrections will be written to, by default
            ColumnInfo.Name.INTENSITY_CORRECTION
        incoming_neutron_column_name : str, optional
            name of column where incoming neutron intensity values are
            stored in the dataframe, by default
            "incoming_neutron_intensity"
        """
        super().__init__(
            correction_type=correction_type,
            correction_factor_column_name=correction_factor_column_name,
        )
        self.incoming_neutron_column_name = incoming_neutron_column_name
        self.reference_incoming_neutron_value = (
            reference_incoming_neutron_value
        )

    def apply(self, data_frame):
        """
        Applies the neutron correction

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame with appropriate data

        Returns
        -------
        pd.DataFrame
            DataFrame now corrected
        """

        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: incoming_intensity_correction(
                incoming_intensity=row[self.incoming_neutron_column_name],
                ref_incoming_intensity=row[
                    self.reference_incoming_neutron_value
                ],
                rc_scaling=1,
            ),
            axis=1,
        )

        return data_frame


class IncomingIntensityCorrectionHawdon2014(Correction):
    """
    Corrects for incoming neutron intensity according to the method
    outlined in Hawdon et al., (2014).

    https://doi.org/10.1002/2013WR015138
    """

    def __init__(
        self,
        ref_incoming_neutron_value: str = str(
            ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE
        ),
        site_cutoff_rigidity: str = str(ColumnInfo.Name.SITE_CUTOFF_RIGIDITY),
        correction_factor_column_name: str = str(
            ColumnInfo.Name.INTENSITY_CORRECTION
        ),
        incoming_neutron_column_name: str = str(
            ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY
        ),
        ref_monitor_cutoff_rigidity: str = str(
            ColumnInfo.Name.REFERENCE_MONITOR_CUTOFF_RIGIDITY
        ),
        rc_correction_factor: str = str(ColumnInfo.Name.RC_CORRECTION_FACTOR),
        correction_type: CorrectionType = CorrectionType.INCOMING_INTENSITY,
    ):
        """

        Parameters
        ----------
        ref_incoming_neutron_value : str, optional
            column name containing the reference incoming neutron value,
            by default str(
            ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE )
        site_cutoff_rigidity : str, optional
            column name containing the site cutoff rigidity, by default
            str(ColumnInfo.Name.SITE_CUTOFF_RIGIDITY)
        correction_factor_column_name : str, optional
            column name where correction factor will be written, by
            default str( ColumnInfo.Name.INTENSITY_CORRECTION )
        incoming_neutron_column_name : str, optional
            column name where incoming neutron intensity values are
            stored , by default str(
            ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY )
        ref_monitor_cutoff_rigidity : str, optional
            Name of the column the reference monitor cutoff rigidity is
            stored, by default str(
            ColumnInfo.Name.REFERENCE_MONITOR_CUTOFF_RIGIDITY )
        rc_correction_factor : str, optional
            name of the column the rc_correction will be written to, by
            default str( ColumnInfo.Name.RC_CORRECTION_FACTOR )
        correction_type : CorrectionType, optional
            The correction type as an Enum, by default
            CorrectionType.INCOMING_INTENSITY
        """
        super().__init__(
            correction_type=correction_type,
            correction_factor_column_name=correction_factor_column_name,
        )
        self.ref_incoming_neutron_value = ref_incoming_neutron_value
        self.site_cutoff_rigidity = site_cutoff_rigidity
        self.ref_monitor_cutoff_rigidity = ref_monitor_cutoff_rigidity
        self.rc_correction_factor = rc_correction_factor
        self.incoming_neutron_column_name = incoming_neutron_column_name

    def _check_required_columns(self, data_frame):
        """
        Checks that the required columns are available.

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame with the data

        Raises
        ------
        ValueError
            Raises when required columns are missing
        """
        required_columns = [
            self.incoming_neutron_column_name,
            self.ref_incoming_neutron_value,
            self.site_cutoff_rigidity,
        ]
        missing_columns = [
            col
            for col in required_columns
            if is_column_missing_or_empty(data_frame, col)
        ]
        if missing_columns:
            raise ValueError(
                f"Required columns are missing or empty: {', '.join(missing_columns)}"
            )

    def _calc_rc_scale_param(self, data_frame):
        """
        Calculates the correction to account for difference in site and
        reference monitor cutoff rigidity.

        Parameters
        ----------
        data_frame : pd.DataFrame
            The DataFrame with the data
        """
        data_frame[self.rc_correction_factor] = data_frame.apply(
            lambda row: rc_correction_hawdon(
                site_cutoff_rigidity=row[self.site_cutoff_rigidity],
                ref_monitor_cutoff_rigidity=row[
                    self.ref_monitor_cutoff_rigidity
                ],
            ),
            axis=1,
        )
        return data_frame

    def apply(self, data_frame):
        """
        Applies the correction factor returning a dataframe with the
        calculated values in it.

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame

        Returns
        -------
        pd.DataFrame
            DataFrame with the correction values attached
        """
        self._check_required_columns(data_frame=data_frame)
        data_frame = self._calc_rc_scale_param(data_frame=data_frame)

        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: incoming_intensity_correction(
                incoming_intensity=row[self.incoming_neutron_column_name],
                ref_incoming_intensity=row[self.ref_incoming_neutron_value],
                rc_scaling=row[self.rc_correction_factor],
            ),
            axis=1,
        )
        return data_frame


class IncomingIntensityCorrectionMcJannetDesilets2023(Correction):
    """
    Corrects for incoming neutron intensity according to the method
    outlined in McJannet and Desilets., (2023).

    https://doi.org/10.1029/2022WR033889
    """

    def __init__(
        self,
        ref_incoming_neutron_value: str = str(
            ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE
        ),
        site_cutoff_rigidity: str = str(ColumnInfo.Name.SITE_CUTOFF_RIGIDITY),
        correction_factor_column_name: str = str(
            ColumnInfo.Name.INTENSITY_CORRECTION
        ),
        incoming_neutron_column_name: str = str(
            ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY
        ),
        latitude: str = str(ColumnInfo.Name.LATITUDE),
        elevation: str = str(ColumnInfo.Name.ELEVATION),
        rc_correction_factor: str = str(ColumnInfo.Name.RC_CORRECTION_FACTOR),
        correction_type: CorrectionType = CorrectionType.INCOMING_INTENSITY,
    ):
        """

        Parameters
        ----------
        ref_incoming_neutron_value : str, optional
            column name containing the reference incoming neutron value,
            by default str(
            ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE )
        site_cutoff_rigidity : str, optional
            column name containing the site cutoff rigidity, by default
            str(ColumnInfo.Name.SITE_CUTOFF_RIGIDITY)
        correction_factor_column_name : str, optional
            column name where correction factor will be written, by
            default str( ColumnInfo.Name.INTENSITY_CORRECTION )
        incoming_neutron_column_name : str, optional
            column name where incoming neutron intensity values are
            stored, by default str(
            ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY )
        latitude : str, optional
            column name where latitude values are stored, by default
            str(ColumnInfo.Name.LATITUDE)
        elevation : str, optional
            column name where elevation values are stored, by default
            str(ColumnInfo.Name.ELEVATION)
        rc_correction_factor : str, optional
            name of the column the rc_correction will be written to, by
            default str(ColumnInfo.Name.RC_CORRECTION_FACTOR)
        correction_type : CorrectionType, optional
            the correction type as an Enum, by default
            CorrectionType.INCOMING_INTENSITY
        """
        super().__init__(
            correction_type=correction_type,
            correction_factor_column_name=correction_factor_column_name,
        )
        self.ref_incoming_neutron_value = ref_incoming_neutron_value
        self.site_cutoff_rigidity = site_cutoff_rigidity
        self.latitude = latitude
        self.elevation = elevation
        self.rc_correction_factor = rc_correction_factor
        self.incoming_neutron_column_name = incoming_neutron_column_name

    def _check_required_columns(self, data_frame):
        """
        Checks that the required columns are available.

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame to check

        Raises
        ------
        ValueError
            Error when needed columns are missing.
        """
        required_columns = [
            self.incoming_neutron_column_name,
            self.ref_incoming_neutron_value,
            self.site_cutoff_rigidity,
            self.latitude,
            self.elevation,
        ]

        missing_columns = [
            col
            for col in required_columns
            if is_column_missing_or_empty(data_frame, col)
        ]
        if missing_columns:
            raise ValueError(
                f"Required columns are missing or empty: {', '.join(missing_columns)}"
            )

    def _check_reference_monitor_is_jung(self, data_frame):
        """
        The reference station in the mcjannet desillets formulation is
        Jungfraujoch. If different reference monitor is supplied, and
        therefore a different reference point, an error is raised.

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame with data
        """
        station_supplied = data_frame[
            str(ColumnInfo.Name.NMDB_REFERENCE_STATION)
        ].iloc[0]
        if station_supplied != "JUNG":
            message = (
                "If using the McjannetDesilets2023 method for incoming intensity correction "
                "only 'JUNG' (Jungfraujoch) can be given as a reference station. \n"
                f"{station_supplied} was given"
            )
            core_logger.error(message)
            raise ValueError(message)

    def _calc_rc_scale_param(self, data_frame):
        """
        Calculates the correction to account for difference in site and
        reference monitor cutoff rigidity.

        Parameters
        ----------
        data_frame : pd.DataFrame
            The DataFrame with the data
        """
        data_frame[self.rc_correction_factor] = data_frame.apply(
            lambda row: McjannetDesilets2023.tau(
                latitude=row[self.latitude],
                elevation=row[self.elevation],
                cut_off_rigidity=row[self.site_cutoff_rigidity],
            ),
            axis=1,
        )
        return data_frame

    def apply(self, data_frame):
        self._check_required_columns(data_frame=data_frame)
        self._check_reference_monitor_is_jung(data_frame=data_frame)
        data_frame = self._calc_rc_scale_param(data_frame=data_frame)

        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: incoming_intensity_correction(
                incoming_intensity=row[self.incoming_neutron_column_name],
                ref_incoming_intensity=row[self.ref_incoming_neutron_value],
                rc_scaling=row[self.rc_correction_factor],
            ),
            axis=1,
        )
        return data_frame


class HumidityCorrectionRosolem2013(Correction):
    """
    Corrects neutrons for humidity according to the
     Rosolem et al. (2013) equation.

    https://doi.org/10.1175/JHM-D-12-0120.1
    """

    def __init__(
        self,
        reference_absolute_humidity_value: float = 0,
        correction_type: str = CorrectionType.HUMIDITY,
        correction_factor_column_name: str = str(
            ColumnInfo.Name.HUMIDITY_CORRECTION
        ),
        sat_vapour_pressure_column_name: str = str(
            ColumnInfo.Name.SATURATION_VAPOUR_PRESSURE
        ),
        air_temperature_column_name: str = str(
            ColumnInfo.Name.AIR_TEMPERATURE
        ),
        actual_vapour_pressure_column_name: str = str(
            ColumnInfo.Name.ACTUAL_VAPOUR_PRESSURE
        ),
        absolute_humidity_column_name: str = str(
            ColumnInfo.Name.ABSOLUTE_HUMIDITY
        ),
        relative_humidity_column_name: str = str(
            ColumnInfo.Name.AIR_RELATIVE_HUMIDITY
        ),
    ):
        """
        Required attributes for creation.

        Parameters
        ----------
        reference_incoming_neutron_value : float
            reference count of incoming neutron intensity at a point in
            time.
        correction_type : str, optional
            correction type, by default "intensity"
        correction_factor_column_name : str, optional
            name of column corrections will be written to, by default
            "correction_for_intensity"
        incoming_neutron_column_name : str, optional
            name of column where incoming neutron intensity values are
            stored in the dataframe, by default
            "incoming_neutron_intensity"
        """
        super().__init__(
            correction_type=correction_type,
            correction_factor_column_name=correction_factor_column_name,
        )
        self.sat_vapour_pressure_column_name = sat_vapour_pressure_column_name
        self.reference_absolute_humidity_value = (
            reference_absolute_humidity_value
        )
        self.air_temperature_column_name = air_temperature_column_name
        self.absolute_humidity_column_name = absolute_humidity_column_name
        self.actual_vapour_pressure_column_name = (
            actual_vapour_pressure_column_name
        )
        self.relative_humidity_column_name = relative_humidity_column_name

    def _check_if_abs_hum_exists(self, data_frame):
        """
        Checks if absolute humidity column exits

        Parameters
        ----------
        data_frame : pd.DataFrame
            Data frame with sensor data

        Returns
        -------
        Bool
            True or False if abs hum col exists.
        """
        if self.absolute_humidity_column_name in data_frame.columns:
            return True
        else:
            return False

    def _create_abs_hum_data(self, data_frame):
        """
        Creates absolute humidity data

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame with CRNS data

        Returns
        -------
        pd.DataFrame
            With additional columns such as absolute humidity
        """
        abs_hum_creator = AbsoluteHumidityCreator(data_frame=data_frame)
        data_frame = abs_hum_creator.check_and_return_abs_hum_column()
        return data_frame

    def apply(self, data_frame):
        """
        Applies the neutron correction

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame with appropriate data

        Returns
        -------
        pd.DataFrame
            DataFrame now corrected
        """

        abs_hum_exists = self._check_if_abs_hum_exists(data_frame=data_frame)
        if not abs_hum_exists:
            data_frame = self._create_abs_hum_data(data_frame=data_frame)

        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: humidity_correction_rosolem2013(
                row[self.absolute_humidity_column_name],
                self.reference_absolute_humidity_value,
            ),
            axis=1,
        )

        return data_frame


class PressureCorrectionZreda2012(Correction):
    """
    Corrects neutrons for changes in atmospheric pressure according to
    the original Zreda et al. (2012) equation.

    https://doi.org/10.5194/hess-16-4079-2012
    """

    def __init__(
        self,
        site_elevation: str = str(ColumnInfo.Name.ELEVATION),
        reference_pressure_value: str = str(ColumnInfo.Name.MEAN_PRESSURE),
        correction_type: str = CorrectionType.PRESSURE,
        correction_factor_column_name: str = str(
            ColumnInfo.Name.PRESSURE_CORRECTION
        ),
        beta_coefficient: str = str(ColumnInfo.Name.BETA_COEFFICIENT),
        latitude: str = str(ColumnInfo.Name.LATITUDE),
        site_cutoff_rigidity: str = str(ColumnInfo.Name.SITE_CUTOFF_RIGIDITY),
    ):
        """
        Required attributes for creation.

        Parameters
        ----------
        site_elevation : float, optional
            site elevation in m, by default None
        reference_pressure_value : float, optional
            reference pressure for correction (recommended to be average
            site pressure). - hPa , by default None
        correction_type : str, optional
            correction type, by default CorrectionType.PRESSURE
        correction_factor_column_name : str, optional
            Name of column to store correction factors, by default str(
            ColumnInfo.Name.PRESSURE_CORRECTION )
        beta_coefficient : float, optional
            beta_coefficient for processing, by default None
        latitude : float, optional
            latitude of site in degrees, by default None
        site_cutoff_rigidity : _type_, optional
            cut-off rigidity at the site, by default None
        """
        super().__init__(
            correction_type=correction_type,
            correction_factor_column_name=correction_factor_column_name,
        )
        self.reference_pressure_value = reference_pressure_value
        self.beta_coefficient = beta_coefficient
        self.site_elevation = site_elevation
        self.latitude = latitude
        self.site_cutoff_rigidity = site_cutoff_rigidity

    def _prepare_for_correction(self, data_frame):
        """
        Prepare to correction process. Check to see if reference
        pressure needs calculating and then checks for coefficients
        given in site information. If no coefficient given it will
        calculate the beta_coefficient.
        """

        self._ensure_reference_pressure_available(data_frame)
        self._check_coefficient_available(data_frame)

    def _ensure_reference_pressure_available(self, data_frame):
        """
        Checks for reference pressure.

        NOTE: Important to note that changing reference pressure from
        the value used during calibration will impact the results.
        If reference pressure is changed for processing the site must be
        re-calibrated so that the N0 has the same reference pressure.

        Raises
        ------
        ValueError
            If no reference pressure and no elevation it cannot work.
            Raises error.
        """
        column_name_press = self.reference_pressure_value
        column_name_elev = self.site_elevation
        if is_column_missing_or_empty(data_frame, column_name_press):
            if is_column_missing_or_empty(data_frame, column_name_elev):
                message = (
                    "You must supply a reference pressure or a site elevation"
                )
                core_logger.error(message)
                raise ValueError(message)
            message = (
                "No reference pressure value given. Calculating average pressure "
                "using elevation information and using this value"
            )
            core_logger.info(message)
            data_frame[self.reference_pressure_value] = data_frame.apply(
                lambda row: calc_mean_pressure(row[self.site_elevation]),
                axis=1,
            )

    def _check_coefficient_available(self, data_frame):
        """
        Checks for coefficient availability. If not available it will
        calculate it using latitude, site elevation and site cutoff
        rigidity.
        """
        column_name_beta = self.beta_coefficient

        if is_column_missing_or_empty(data_frame, column_name_beta):
            message = (
                "No coefficient given for pressure correction. "
                "Calculating beta coefficient."
            )
            core_logger.info(message)
            data_frame[self.beta_coefficient] = data_frame.apply(
                lambda row: calc_beta_coefficient(
                    row[self.reference_pressure_value],
                    row[self.latitude],
                    row[self.site_elevation],
                    row[self.site_cutoff_rigidity],
                ),
                axis=1,
            )

    def apply(self, data_frame):
        """
        Applies the neutron correction

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame with appropriate data

        Returns
        -------
        pd.DataFrame
            DataFrame now corrected
        """

        # TODO validation here

        if not is_column_missing_or_empty(
            data_frame, self.correction_factor_column_name
        ):
            message = (
                "The correction already appears in the data_frame as"
                f"'{self.correction_factor_column_name}'. Skipping correction to prevent "
                "unwanted overwrites. "
            )
            core_logger.info(message)
            return data_frame
        else:
            self._prepare_for_correction(data_frame)
            data_frame[self.correction_factor_column_name] = data_frame.apply(
                lambda row: calc_pressure_correction_beta_coeff(
                    row[str(ColumnInfo.Name.AIR_PRESSURE)],
                    row[self.reference_pressure_value],
                    row[self.beta_coefficient],
                ),
                axis=1,
            )
            return data_frame


class AboveGroundBiomassCorrectionBaatz2015(Correction):

    def __init__(
        self,
        correction_type: CorrectionType,
        correction_factor_column_name: str,
        above_ground_biomass_column_name: str,
    ):
        super().__init__(
            correction_type=correction_type,
            correction_factor_column_name=correction_factor_column_name,
        )
        self.above_ground_biomass_column_name = (
            above_ground_biomass_column_name
        )

    def apply(self, data_frame):
        print(
            f"{self.above_ground_biomass_column_name} needs to be in units of "
            "kg m^2."
        )
        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: above_ground_biomass_correction_baatz2015(
                above_ground_biomass=row[self.above_ground_biomass_column_name]
            ),
            axis=1,
        )

        return data_frame


class AboveGroundBiomassCorrectionMorris2024(Correction):
    """_summary_



    https://doi.org/10.3390/s24134094
    """

    def __init__(
        self,
        correction_type: CorrectionType,
        correction_factor_column_name: str,
        above_ground_biomass_column_name: str,
    ):
        super().__init__(
            correction_type=correction_type,
            correction_factor_column_name=correction_factor_column_name,
        )
        self.above_ground_biomass_column_name = (
            above_ground_biomass_column_name
        )

    def apply(self, data_frame):
        print(
            f"{self.above_ground_biomass_column_name} needs to be in units of "
            "mm (i.e., Biomass Water Equivalant)."
        )
        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: above_ground_biomass_correction_morris2024(
                above_ground_biomass=row[self.above_ground_biomass_column_name]
            ),
            axis=1,
        )

        return data_frame
