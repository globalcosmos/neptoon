import pandas as pd
from abc import ABC, abstractmethod
from neptoon.logging import get_logger

# read in the specific functions here
from neptoon.corrections_and_functions.incoming_intensity_corrections import (
    incoming_intensity_zreda_2012,
)


core_logger = get_logger()


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
        correction_type: str = "intensity",
        correction_factor_column_name: str = "correction_for_intensity",
        incoming_neutron_column_name: str = "incoming_neutron_intensity",
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
        self.incoming_neutron_column_name = incoming_neutron_column_name
        self.reference_incoming_neutron_value = (
            reference_incoming_neutron_value
        )
        self.correction_factor_column_name = correction_factor_column_name
        self.correction_type = correction_type

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
        # TODO validation here??
        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: incoming_intensity_zreda_2012(
                row[self.incoming_neutron_column_name],
                self.reference_incoming_neutron_value,
            ),
            axis=1,
        )

        return data_frame
