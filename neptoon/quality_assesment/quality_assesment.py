from saqc import SaQC
import pandas as pd
from neptoon.logging import get_logger
from abc import abstractmethod, ABC
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
    """

    @abstractmethod
    def apply(self, qc):
        pass


class FlagRangeCheck(QualityCheck):
    """
    Creates a check using the flagRange check from SaQC. By wrapping the
    check in this way we can implement the log_key_step for
    DataAuditLog.

    """

    @log_key_step("column", "min_val", "max_val")
    def __init__(self, column, min_val, max_val):
        self.column = column
        self.min_val = min_val
        self.max_val = max_val

    def apply(self, qc: SaQC):
        return qc.flagRange(
            field=self.column, min=self.min_val, max=self.max_val
        )


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
