import pandas as pd
from enum import Enum
from abc import ABC, abstractmethod
from neptoon.logging import get_logger
from neptoon.data_management.column_names import ColumnInfo

# read in the specific functions here
from neptoon.corrections_and_functions.incoming_intensity_corrections import (
    incoming_intensity_zreda_2012,
)

from neptoon.corrections_and_functions.air_humidity_corrections import (
    calc_absolute_humidity,
    calc_saturation_vapour_pressure,
    calc_actual_vapour_pressure,
    humidity_correction_rosolem2013,
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


class IncomingIntensityZreda(Correction):
    """
    Corrects neutrons for incoming neutron intensity according to the
    original Zreda et al. (2012) equation.

    https://doi.org/10.5194/hess-16-4079-2012
    """

    def __init__(
        self,
        reference_incoming_neutron_value: float,
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
                self.reference_incoming_neutron_value,
            ),
            axis=1,
        )

        return data_frame


class HumidityCorrectionRosolem2012(Correction):
    """
    Corrects neutrons for incoming neutron intensity according to the
    original Zreda et al. (2012) equation.

    https://doi.org/10.5194/hess-16-4079-2012
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
