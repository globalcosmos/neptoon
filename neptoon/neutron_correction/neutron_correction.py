import pandas as pd
from abc import ABC, abstractmethod
from neptoon.logging import get_logger

# we read in the specific functions here
from neptoon.corrections_and_functions.incoming_intensity_corrections import (
    incoming_intensity_zreda_2012,
)

core_logger = get_logger()


class Correction(ABC):
    """
    Expects a dataframe as input and then applies corrections and
    updates df

    """

    def __init__(self):
        pass

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


class IncomingIntensityDesilets(Correction):

    def __init__(
        self,
        reference_incoming_neutron_value: float,
        incoming_neutron_column_name: str = "incoming_neutron_intensity",
    ):
        self.incoming_neutron_column_name = incoming_neutron_column_name
        self.reference_incoming_neutron_value = (
            reference_incoming_neutron_value
        )

    def apply(self, data_frame):
        """
        Applies the neutron correction

        Parameters
        ----------
        data_frame : _type_
            _description_

        Returns
        -------
        _type_
            _description_
        """
        # validation here??
        data_frame["intensity_correction"] = data_frame.apply(
            lambda row: incoming_intensity_zreda_2012(
                row[self.incoming_neutron_column_name],
                self.reference_incoming_neutron_value,
            )
        )

        return data_frame


class CorrectionBuilder:
    """
    Staging place for the corrections as they are built. First a user
    adds a check using the add_check method.
    """

    def __init__(self):
        self.correction = []

    def add_correction(self, correction):
        if isinstance(correction, Correction):
            self.checks.append(correction)
        return self

    def apply_correction(self, df):
        for correction in self.correction:
            df = correction.apply(df)
        return df


class CorrectNeutrons:

    def __init__(
        self,
        crns_data_frame: pd.DataFrame,
        correction_steps: CorrectionBuilder,
    ):
        self._crns_data_frame = crns_data_frame

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_Data_frame(self, df: pd.DataFrame):
        # TODO add checks it is df
        self._crns_data_frame = df

    def correct_neutrons(self):
        pass
