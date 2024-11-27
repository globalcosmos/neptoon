from saqc import SaQC
import pandas as pd
from dataclasses import dataclass
from abc import abstractmethod, ABC
from typing import Union, Dict, Any, Set
from enum import Enum
from neptoon.logging import get_logger
from neptoon.data_audit import log_key_step
from neptoon.columns import ColumnInfo

core_logger = get_logger()


class DateTimeIndexValidator:
    """
    Validator class which checks that the supplied data frame has a
    datetime index
    """

    def __init__(self, data_frame: pd.DataFrame):
        """
        Init

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame to be checked
        """
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


class ValidationError(Exception):
    """Simple validation error"""

    pass


class SaQCMethodMap(Enum):
    RANGE_CHECK = "flagRange"
    SPIKE_UNIOLOF = "flagUniLOF"


class QAStage(Enum):
    RAW_NEUTRON = "raw_neutrons"
    INPUT_VARIABLES = "input_variables"
    CORRECTED_NEUTRONS = "corrected_neutrons"
    DERIVED_PRODUCTS = "derived_products"


class Params(ABC):

    def __init__(
        self,
        params_dict: Dict[str, Any],
    ):
        self.params_dict = params_dict
        self._validate_params()

    # Child classes must define these
    ESSENTIAL_PARAMS: list[str] = []
    OPTIONAL_PARAMS: list[str] = []

    def _validate_params(self) -> None:
        """
        Check params against essential and optional lists
        """
        missing = set(self.ESSENTIAL_PARAMS) - set(self.params_dict.keys())
        if missing:
            raise ValidationError(f"Missing essential parameters: {missing}")

        allowed = set(self.ESSENTIAL_PARAMS + self.OPTIONAL_PARAMS)
        unknown = set(self.params_dict.keys()) - allowed
        if unknown:
            raise ValidationError(f"Unknown parameters provided: {unknown}")


@dataclass
class RangeCheckParams(Params):

    min: float
    max: float
    column_name: str


@dataclass
class UniLofParams(Params):
    min: float
    max: float
    column_name: str


class QualityCheck:
    """
    Creates quality check.

    A class above this would create the check by mapping the
    yaml/supplied info to the created enums:

    flag_raw_neutrons: <-- QAStage
        spikes: <-- this is SaQCMethodMap
            col_name: default               |
            method: UniLOF                  |
            periods_in_calculation: 24      | <-- params
            threshold: 1.2                  |
    """

    PARAM_MAPPING = {
        SaQCMethodMap.RANGE_CHECK: RangeCheckParams,
        SaQCMethodMap.SPIKE_UNIOLOF: UniLofParams,
    }

    def __init__(
        self,
        stage,
        method: SaQCMethodMap,
        raw_params: str,  # obj
    ):
        self.method = method
        self.raw_params = raw_params
        self.param_dict = self._create_param_dict(raw_params=raw_params)

    def _create_param_dict(self, raw_params):
        # based on method, know how to set params
        pass

    def apply(self):
        method = getattr(SaQC, method.value)
        return method(**self.param_set)


class QualityCheck(ABC):
    """
    Base method for quality check wrappers.
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
    def __init__(
        self,
        column_name: str,
        min_val: Union[int | float],
        max_val: Union[int | float],
    ):
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
        self.column_name = column_name
        self.min_val = min_val
        self.max_val = max_val

    def apply(self, qc: SaQC):
        return qc.flagRange(
            field=self.column_name, min=self.min_val, max=self.max_val
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
    def __init__(
        self,
        N0: Union[int | float],
        column_name: str = str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ),
        above_N0_factor: float = 1,
    ):
        """
        Init Values

        Parameters
        ----------
        N0 : int | float
            The N0 number neutrons cannot exceed.
        neutron_col_name : str
            Column name to flag
        """
        self.column_name = column_name
        self.N0 = N0
        self.above_N0_factor = above_N0_factor

    def apply(self, qc: SaQC):
        no_greater_than = self.N0 * self.above_N0_factor
        return qc.flagGeneric(
            field=self.column_name, func=lambda x: x > no_greater_than
        )


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
        N0: Union[int | float],
        percent_minimum: Union[int | float] = 0.3,
        column_name: str = str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ),
    ):
        """
        Init Values

        Parameters
        ----------
        N0 : Union[int  |  float]
            The NO calibration term of the site
        percent_minimum : Union[int  |  float], optional
            The decimal percent value which, by default 0.3
        neutron_col_name : str, optional
            name of column where corrected neutrons are stored, by
            default str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
                            )
        """
        self.column_name = column_name
        self.N0 = N0
        self.percent_minimum = percent_minimum

    def apply(self, qc: SaQC):
        return qc.flagGeneric(
            field=self.column_name,
            func=lambda x: x < (self.N0 * self.percent_minimum),
        )


class FlagSpikeDetectionUniLOF(QualityCheck):
    """
    Build the flag routine to detect outliers

    Returns
    -------
    SaQC
        SaQC object with flags
    """

    @log_key_step("column_name", "periods_in_calculation", "threshold")
    def __init__(
        self,
        column_name: str,
        periods_in_calculation: Union[int | float] = 24,
        threshold: Union[int | float] = 1.2,
    ):
        """
        Initialisation parameters

        Parameters
        ----------
        column_name : str
            Name of the column to flag
        periods_in_calculation : int
            Number of nearest neightbours to calculate flagging
        threshold : float
            Threshold value (default 1.5 based on SaQC recommendation)
        """
        self.column_name = column_name
        self.periods_in_calculation = periods_in_calculation
        self.threshold = threshold

    def apply(self, qc=SaQC):
        return qc.flagUniLOF(
            self.column_name,
            n=self.periods_in_calculation,
            thresh=self.threshold,
        )


class FlagPersistance(QualityCheck):
    def __init__(
        self,
        column_name: str,
        threshold: float,
        window: int | str,
        min_periods: int = 2,
    ):
        self.column_name = column_name
        self.threshold = threshold
        self.window = window
        self.min_periods = min_periods

    def apply(self, qc=SaQC):
        return qc.flagConstants(
            field=self.column_name,
            thresh=self.threshold,
            window=self.window,
            min_periods=self.min_periods,
        )


class QualityAssessmentFlagBuilder:
    """
    Staging place for the checks as they are built. First a user adds a
    check using the add_check method.
    """

    def __init__(self):
        self.checks = []

    def add_check(self, *checks):
        for check in checks:
            if isinstance(check, QualityCheck):
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

    def __init__(
        self,
        data_frame: pd.DataFrame,
        saqc_scheme: str = "simple",
        saqc: SaQC = None,
    ):
        """
        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame containing time series data.
        """
        DateTimeIndexValidator(data_frame=data_frame)
        self.data_frame = data_frame
        self.saqc_scheme = saqc_scheme
        self._builder = QualityAssessmentFlagBuilder()
        self._check_for_saqc(saqc)

    @property
    def builder(self):
        return self._builder

    @builder.setter
    def builder(self, builder: QualityAssessmentFlagBuilder):
        """
        Enforce the self.builder to be a QualityAssessmentFlagBuilder.
        """
        if not isinstance(builder, QualityAssessmentFlagBuilder):
            message = (
                "Expected QualityAssessmentFlagBuilder, "
                f" got {type(builder).__name__}"
            )
            core_logger.error(message)
            raise ValueError(message)
        self._builder = builder

    def _check_for_saqc(self, saqc):
        """
        Checks the saqc object. If None provided it will create one,
        otherwise it will use the supplied SaQC object.

        Parameters
        ----------
        saqc : SaQC | None
            An SaQC object or None
        """
        if saqc is None:
            self.qc = SaQC(self.data_frame, scheme=self.saqc_scheme)
        elif isinstance(saqc, SaQC):
            self.qc = saqc
        else:
            message = (
                f"{saqc} does not appear to be an SaQC object."
                " Please leave saqc as blank or import an SaQC object"
            )
            core_logger.error(message)
            print(message)

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
        """
        Cycles through the quality checks in the builder applying each
        of them to the data frame
        """
        self.qc = self.builder.apply_checks(self.qc)

    def add_custom_flag_builder(self, builder: QualityAssessmentFlagBuilder):
        """
        Add a custom built flag builder to the object.

        Parameters
        ----------
        builder : QualityAssessmentFlagBuilder
            A flag builder - presumed to be pre-constructed
        """
        self.builder = builder

    def add_quality_check(self, check):
        """
        Can be a check or a list of checks to the internal
        QualitCheckBuilder

        Parameters
        ----------
        check : QualityCheck | List of QualityCheck
            Quality checks
        """
        self.builder.add_check(check)

    def import_checks_from_config(self, config):
        """
        Here could be a function for building the quality checks from a
        supplied config file
        """
        # Check config has correct values with pydantic validation
        # Build Flag Builder
        # Apply flags
        pass

    def return_data_frame(self):
        """
        Returns the timeseries DataFrame.

        Returns
        -------
        pd.DataFrame
            The main DataFrame
        """
        return self.qc.data.to_pandas()

    def return_flags_data_frame(self):
        """
        Returns the flag dataframe

        Returns
        -------
        pd.DataFrame
            The DataFrame with assigned flags
        """
        return self.qc.flags.to_pandas()
