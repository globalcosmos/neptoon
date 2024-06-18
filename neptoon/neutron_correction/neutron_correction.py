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
    Expects a dataframe as input and then applies corrections and
    updates df
    """

    def __init__(self, correction_type: str):
        self._correction_factor_column_name = None
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


class IncomingIntensityDesilets(Correction):

    def __init__(
        self,
        reference_incoming_neutron_value: float,
        correction_type: str = "intensity",
        correction_factor_column_name: str = "correction_for_intensity",
        incoming_neutron_column_name: str = "incoming_neutron_intensity",
    ):
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
        data_frame : _type_
            _description_

        Returns
        -------
        _type_
            _description_
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


class CorrectionBuilder:
    """
    Staging place for the corrections as they are built. First a user
    adds a check using the add_check method.
    """

    def __init__(self):
        self.corrections = {}
        self.correction_columns = []

    def add_correction(self, correction: Correction):
        """
        Adds a correction to the CorrectionBuilder

        Parameters
        ----------
        correction : Correction
            A Correction object
        """
        if isinstance(correction, Correction):
            correction_type = correction.correction_type
            self.corrections[correction_type] = correction

    def remove_correction_by_type(self, correction_type: str):
        """
        Removes a correction from the CorrectionBuilder based on its type

        Parameters
        ----------
        correction_type : str
            The type of correction to be removed
        """
        if correction_type in self.corrections:
            correction = self.corrections.pop(correction_type)
            correction_column_name = (
                correction.get_correction_factor_column_name()
            )
            if correction_column_name in self.correction_columns:
                self.correction_columns.remove(correction_column_name)
        else:
            raise ValueError(
                f"Correction type '{correction_type}' not found in the builder."
            )

    def get_corrections(self):
        """
        Returns the corrections stored in the builder
        """
        return self.corrections.values()


class CorrectNeutrons:

    def __init__(
        self,
        crns_data_frame: pd.DataFrame,
        correction_builder: CorrectionBuilder,
    ):
        self._crns_data_frame = crns_data_frame
        self._correction_builder = correction_builder
        self._correction_columns = []

    @property
    def crns_data_frame(self):
        return self._crns_data_frame

    @crns_data_frame.setter
    def crns_Data_frame(self, df: pd.DataFrame):
        # TODO add checks that it is df
        self._crns_data_frame = df

    @property
    def correction_builder(self):
        return self._correction_builder

    @correction_builder.setter
    def correction_builder(self, builder: CorrectionBuilder):
        if isinstance(builder, CorrectionBuilder):
            self._correction_builder = builder
        else:
            message = f"It appears {builder} is not a CorrectionBuilder object"
            core_logger.error(message)

    @property
    def correction_columns(self):
        return self._correction_columns

    def add_correction(self, new_correction: Correction):
        """
        Add an invidual correction to the CorrectionBuilder

        Parameters
        ----------
        new_correction : Correction
            The new correction to apply
        """
        self.correction_builder.add_correction(new_correction)

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
        self.correction_builder = new_correction_builder

    def create_correction_factors(self, df: pd.DataFrame):
        """
        Cycles through all the corrections in the CorrectionBuilder and
        applies them to the DataFrame. Returns the DataFrame with additional
        columns.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame which is prepared for correction.

        Returns
        -------
        pd.DataFrame
            DataFrame with additional columns applied during correction.
        """
        for correction in self.correction_builder.get_corrections():
            df = correction.apply(df)
            correction_column_name = (
                correction.get_correction_factor_column_name()
            )
            self.correction_columns.append(correction_column_name)

        return df

    def create_corrected_neutron_column(self, df):
        df["corrected_epithermal_neutron_count"] = df["epithermal_neutrons"]
        for column_name in self.correction_columns:
            df["corrected_epithermal_neutron_count"] = (
                df["corrected_epithermal_neutron_count"] * df[column_name]
            )
        return df

    def correct_neutrons(self):
        """
        Corrects neutrons using the CorrectionBuilder. Returns the
        DataFrame.

        Returns
        -------
        df: pd.DataFrame
            DataFrame returned with additional columns.
        """
        df = self.create_correction_factors(self.crns_data_frame)
        df = self.create_corrected_neutron_column(df)
        return df
