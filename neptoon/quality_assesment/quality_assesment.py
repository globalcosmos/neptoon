from saqc import SaQC
import pandas as pd
from abc import abstractmethod, ABC
from typing import Union
from neptoon.logging import get_logger
from neptoon.data_management.data_audit import log_key_step

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


class QualityCheck(ABC):
    """
    Base method for quality check wrappers.

    Ensures they all have an apply function.
    """

    @abstractmethod
    def apply(self, qc):
        """
        Apply the flagging

        Parameters
        ----------
        qc : SaQC
            SaQC to flag with

        Returns
        -------
        qc : SaQC
            SaQC after flagging
        """
        pass


class FlagRangeCheck(QualityCheck):
    """
    Creates a check using the flagRange check from SaQC.

    Returns
    -------
    qc
        SaQC object after flagging
    """

    @log_key_step("column", "min_val", "max_val")
    def __init__(self, column: str, min_val: float, max_val: float):
        """
        Variables

        Parameters
        ----------
        column : str
            Column to flag
        min_val : float
            Minimum value allowed
        max_val : float
            Maximum value allowed
        """
        self.column = column
        self.min_val = min_val
        self.max_val = max_val

    def apply(self, qc: SaQC):
        return qc.flagRange(
            field=self.column, min=self.min_val, max=self.max_val
        )


class FlagNeutronGreaterThanN0(QualityCheck):
    """
    Flag neutron count rates that are greater than N0.

    Returns
    -------
    qc
        Returns the SaQC file after applying flags.
    """

    @log_key_step("neutron_col_name")
    def __init__(self, neutron_col_name: str, N0: Union[int | float]):
        """
        Init Values

        Parameters
        ----------
        neutron_col_name : str
            Column name to flag
        N0 : int | float
            The N0 number neutrons cannot exceed.
        """
        self.column = neutron_col_name
        self.N0 = N0

    def apply(self, qc: SaQC):
        return qc.flagGeneric(field=self.column, func=lambda x: x > self.N0)


class FlagBelowMinimumPercentN0(QualityCheck):
    """
    Flag neutron count rates that are below a threshold percentage of
    N0.

    Neutron

    Returns
    -------
    qc
        Returns the SaQC file after applying flags.
    """

    @log_key_step("neutron_col_name", "percent_minimum")
    def __init__(
        self,
        neutron_col_name: str,
        N0: Union[int | float],
        percent_minimum: float,
    ):
        """
        Init Values

        Parameters
        ----------
        neutron_col_name : str
            Column name to flag
        N0 : int | float
            The N0 number neutrons cannot exceed.
        """
        self.column = neutron_col_name
        self.N0 = N0
        self.percent_minimum = percent_minimum

    def apply(self, qc: SaQC):
        return qc.flagGeneric(
            field=self.column,
            func=lambda x: x > (self.N0 / self.percent_minimum),
        )


# class FlagSpikeDetection


class QualityAssessmentFlagBuilder:
    """
    Staging place for the checks as they are built. First a user adds a
    check using the add_check method.
    """

    def __init__(self):
        self.checks = []

    def add_check(self, check: QualityCheck):
        self.checks.append(check)
        return self

    def apply_checks(self, qc):
        for check in self.checks:
            qc = check.apply(qc)
        return qc


class DataQualityAssessor:
    """
    Base class for working with SaQC in neptoon. It handles creating the
    object and checks that the data going in has a datetime index
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
        self.builder = QualityAssessmentFlagBuilder()

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

    def apply_quality_assessment(self):
        self.qc = self.builder.apply_checks(self.qc)

    def add_quality_check(self, check: QualityCheck):
        self.builder.add_check(check)

    def output_data(self):
        """_summary_

        Returns
        -------
        _type_
            _description_
        """
        return self.qc.data.to_pandas()

    def output_flags(self):
        """_summary_

        Returns
        -------
        _type_
            _description_
        """
        return self.qc.flags.to_pandas()
