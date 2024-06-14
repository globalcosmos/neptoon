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
        # TODO validation here??
        data_frame["intensity_correction"] = data_frame.apply(
            lambda row: incoming_intensity_zreda_2012(
                row[self.incoming_neutron_column_name],
                self.reference_incoming_neutron_value,
            ),
            axis=1,
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
            self.correction.append(correction)
        return self

    def apply_corrections(self, df):
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
        self._correction_steps = correction_steps

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_Data_frame(self, df: pd.DataFrame):
        # TODO add checks that it is df
        self._crns_data_frame = df

    @property
    def correction_steps(self):
        return self._correction_steps

    @correction_steps.setter
    def correction_steps(self, steps: CorrectionBuilder):
        if isinstance(steps, CorrectionBuilder):
            self._correction_steps = steps
        else:
            message = f"It appears {steps} is not a CorrectionBuilder object"
            core_logger.error(message)

    def add_correction(self, new_correction: Correction):
        """
        Add an invidual correction to the CorrectionBuilder

        Parameters
        ----------
        new_correction : Correction
            The new correction to apply
        """
        self.correction_steps.add_correction(new_correction)

    def add_correction_builder(
        self, new_correction_builder: CorrectionBuilder
    ):
        """
        Add a whole correction builder. Useful if a correction builder
        has been built somewhere in the code and you want to read it in.

        Parameters
        ----------
        new_correction_builder : CorrectionBuilder
            A pre-compiled correction builder.
        """
        self.correction_steps = new_correction_builder

    def correct_neutrons(self):
        return self.correction_steps.apply_corrections(self.crns_data_frame)
