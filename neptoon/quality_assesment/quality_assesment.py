from saqc import SaQC
import pandas as pd
from neptoon.logging import get_logger
from abc import abstractmethod, ABC

core_logger = get_logger()


class DateTimeIndexValidator:
    def __init__(self, data_frame: pd.DataFrame):
        self._validate_timestamp_index(data_frame)

    def _validate_timestamp_index(self, data_frame):
        """
        Checks that the index of the dataframe is timestamp (essential
        for using SaQC)

        Parameters
        ----------
        data_frame : pd.DataFrame
            The data frame imported into the TimeStampAligner

        Raises
        ------
        ValueError
            If the index is not datetime type.
        """
        if not pd.api.types.is_datetime64_any_dtype(data_frame.index):
            core_logger.error("DataFrame index not datetime type")
            raise ValueError("The DataFrame index must be of datetime type")


class DataQualityAssessor:
    """
    Base class for working with SaQC in neptoon. It handles creating the
    object which checks that the data going in has a datetime index
    (essential for working in SaQC).

    """

    def __init__(self, data_frame: pd.DataFrame, saqc_scheme: str = "scheme"):
        """
        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame containing time series data.
        """
        DateTimeIndexValidator(data_frame=data_frame)
        self.data_frame = data_frame
        self.saqc_scheme = saqc_scheme
        self.qc = SaQC(self.data_frame, scheme=self.saqc_scheme)

    def change_saqc_scheme(self, scheme: str):
        """
        Changes the saqc_scheme for SaQC object.

        Parameters
        ----------
        scheme : str
            String representing the scheme for flags. Can be:
                - simple
                - float
                - dmp
                - positional
                - annotated-float

            see https://rdm-software.pages.ufz.de/saqc/index.html
        """

        self.saqc_scheme = scheme
        self.qc = SaQC(self.data_frame, scheme=self.saqc_scheme)
        core_logger.info(f"Changed SaQC scheme to {scheme}")

    def output_data(self):
        pass

    def output_flags(self):
        pass

    def apply_quality_assessment(self):
        pass


class QualityAssessmentFlagBuilder(ABC):

    def relative_humidity(self):
        pass
