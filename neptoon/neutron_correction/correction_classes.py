import pandas as pd
from enum import Enum
from abc import ABC, abstractmethod
from neptoon.logging import get_logger
from neptoon.data_management.column_information import ColumnInfo

# read in the specific functions here
from neptoon.corrections_and_functions.incoming_intensity_corrections import (
    incoming_intensity_zreda_2012,
    incoming_intensity_adjustment_rc_corrected,
)

from neptoon.corrections_and_functions.air_humidity_corrections import (
    calc_absolute_humidity,
    calc_saturation_vapour_pressure,
    calc_actual_vapour_pressure,
    humidity_correction_rosolem2013,
)
from neptoon.corrections_and_functions.pressure_corrections import (
    calc_pressure_correction_beta_coeff,
    calc_pressure_correction_l_coeff,
    calc_mean_pressure,
    calc_beta_coefficient,
)

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

    ZREDA_2012 = "zreda_2012"
    ROSOLEM_2013 = "rosolem_2013"
    HAWDON_2014 = "hawdon_2014"
    # TODO the rest


class Correction(ABC):
    """
    Abstract class for the Correction classes. Ensures that all
    corrections have an apply method which takes a DataFrame as an
    argument. The return of the apply function should be a DataFrame
    with the correction factor calculated and added as a column. The
    correction_factor_column_name should be set which is the name of the
    column the correction factor will be recorded into.

    The CorrectionBuilder class will then store the name of columns
    where correction factors are stored. This enables the creation of
    the overall corrected neutron count column.
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

        # TODO validation here

        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: incoming_intensity_zreda_2012(
                row[self.incoming_neutron_column_name],
                row[self.reference_incoming_neutron_value],
            ),
            axis=1,
        )

        return data_frame


class IncomingIntensityCorrectionHawdon2014(Correction):

    def __init__(
        self,
        reference_incoming_neutron_value: str = str(
            ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE
        ),
        cutoff_rigidity: str = str(ColumnInfo.Name.CUTOFF_RIGIDITY),
        correction_type: CorrectionType = CorrectionType.INCOMING_INTENSITY,
        correction_factor_column_name: str = str(
            ColumnInfo.Name.INTENSITY_CORRECTION
        ),
        incoming_neutron_column_name: str = str(
            ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY
        ),
    ):
        super().__init__(
            correction_type=correction_type,
            correction_factor_column_name=correction_factor_column_name,
        )
        self.reference_incoming_neutron_value = (
            reference_incoming_neutron_value
        )
        self.cutoff_rigidity = cutoff_rigidity
        self.incoming_neutron_column_name = incoming_neutron_column_name

    def apply(self, data_frame):
        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: incoming_intensity_adjustment_rc_corrected(
                incoming_intensity=row[self.incoming_neutron_column_name],
                incoming_ref=row[self.incoming_neutron_intensity],
                cutoff_rigidity=row[self.cutoff_rigidity],
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

        data_frame[self.sat_vapour_pressure_column_name] = data_frame.apply(
            lambda row: calc_saturation_vapour_pressure(
                row[self.air_temperature_column_name],
            ),
            axis=1,
        )

        data_frame[self.actual_vapour_pressure_column_name] = data_frame.apply(
            lambda row: calc_actual_vapour_pressure(
                row[self.sat_vapour_pressure_column_name],
                row[self.relative_humidity_column_name],
            ),
            axis=1,
        )

        data_frame[self.absolute_humidity_column_name] = data_frame.apply(
            lambda row: calc_absolute_humidity(
                row[self.actual_vapour_pressure_column_name],
                row[self.air_temperature_column_name],
            ),
            axis=1,
        )

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
        l_coefficient: str = str(ColumnInfo.Name.L_COEFFICIENT),
        latitude: str = str(ColumnInfo.Name.LATITUDE),
        cutoff_rigidity: str = str(ColumnInfo.Name.CUTOFF_RIGIDITY),
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
        l_coefficient : float, optional
            mass attenuation length, by default None
        latitude : float, optional
            latitude of site in degrees, by default None
        cutoff_rigidity : _type_, optional
            cut-off rigidity at the site, by default None
        """
        super().__init__(
            correction_type=correction_type,
            correction_factor_column_name=correction_factor_column_name,
        )
        self.reference_pressure_value = reference_pressure_value
        self.beta_coefficient = beta_coefficient
        self.l_coefficeint = l_coefficient
        self.site_elevation = site_elevation
        self.latitude = latitude
        self.cutoff_rigidity = cutoff_rigidity

    def _prepare_for_correction(self, data_frame):
        """
        Prepare to correction process. Check to see if reference
        pressure needs calculating and then checks for coefficients
        given in site information. If no coefficient given it will
        calculate the beta_coefficient.
        """

        self._ensure_reference_pressure_available(data_frame)
        self._check_coefficient_available(data_frame)

    @staticmethod
    def _is_column_missing_or_empty(data_frame, column_name):
        """
        Find whether a column is missing or empy

        Parameters
        ----------
        data_frame : pd.DataFrame
            _description_
        column_name : str
            Name of column to check for

        Returns
        -------
        _type_
            _description_
        """
        return (
            column_name not in data_frame.columns
            or data_frame[column_name].isnull().all()
        )

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
        if self._is_column_missing_or_empty(data_frame, column_name_press):
            if self._is_column_missing_or_empty(data_frame, column_name_elev):
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
        Checks for coefficients. If none given it will create the
        beta_coefficient from supplied data.
        """
        column_name_beta = self.beta_coefficient
        column_name_l = self.l_coefficeint

        if self._is_column_missing_or_empty(
            data_frame, column_name_beta
        ) and self._is_column_missing_or_empty(data_frame, column_name_l):
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
                    row[self.cutoff_rigidity],
                ),
                axis=1,
            )

            self.method_to_use = "beta"
        elif self._is_column_missing_or_empty(data_frame, column_name_beta):
            self.method_to_use = "beta"
        elif self._is_column_missing_or_empty(data_frame, column_name_l):
            self.method_to_use = "l_coeff"

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

        self._prepare_for_correction(data_frame)

        if self.method_to_use == "beta":
            data_frame[str(ColumnInfo.Name.PRESSURE_CORRECTION)] = (
                data_frame.apply(
                    lambda row: calc_pressure_correction_beta_coeff(
                        row[str(ColumnInfo.Name.AIR_PRESSURE)],
                        row[self.reference_pressure_value],
                        row[self.beta_coefficient],
                    ),
                    axis=1,
                )
            )
        elif self.method_to_use == "l_coeff":
            data_frame[str(ColumnInfo.Name.PRESSURE_CORRECTION)] = (
                data_frame.apply(
                    lambda row: calc_pressure_correction_l_coeff(
                        row[str(ColumnInfo.Name.AIR_PRESSURE)],
                        row[self.reference_pressure_value],
                        row[self.l_coefficeint],
                    ),
                    axis=1,
                )
            )

        return data_frame
