from saqc import SaQC
import pandas as pd
from dataclasses import dataclass
from abc import abstractmethod, ABC
from typing import Union, Dict, Type, TYPE_CHECKING, Optional, Any, Set
from enum import Enum
from neptoon.logging import get_logger
from neptoon.data_audit import log_key_step
from neptoon.columns import ColumnInfo
from neptoon.quality_control.saqc_methods_and_params import *

if TYPE_CHECKING:
    from neptoon.config.configuration_input import ConfigurationObject

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
    """Custom exception for validation errors."""

    pass


class QualityCheck:
    """
    Creates quality check.

    Examples
    --------
    Create a quality check that flags neutron intensity values outside the range 500-550:

    >>> from neptoon.column_info import ColumnInfo
    >>> from neptoon.quality_control import QualityCheck, QAMethod
    >>>
    >>> check = QualityCheck(
    ...     target=QATarget.RAW_NEUTRONS,
    ...     method=QAMethod.RANGE_CHECK,
    ...     params={
    ...         "lower_bound": 500,
    ...         "upper_bound": 550,
    ...     },
    ... )
    """

    @log_key_step("target", "method", "raw_params")
    def __init__(
        self,
        target: QATarget,
        method: QAMethod,
        parameters: Union[dict, "ConfigurationObject"],
    ):
        self.target = target
        self.method = method
        self.parameters = parameters
        self.possible_parameters = self._get_possible_parameters()
        self._validate_essential_params_present()
        self._validate_if_unknown_params_supplied()
        self._set_column_name()
        self.saqc_param_dict = self._convert_to_saqc_names(
            parameters=parameters
        )

    def _get_possible_parameters(self):
        return ParameterRegistry.get_parameter_class(self.method)

    def _convert_to_saqc_names(self, parameters):
        # check if obj or dict
        # get optional info
        # if obj convert to dict

        # check method and pull mapping class
        # map keys from dict to match SaQC method
        # save
        return parameters  # TEMP

    def _validate_essential_params_present(self):
        """
        Checks if essential parameter are supplied.

        Raises
        ------
        ValidationError
            When essential parameter is missing.
        """
        for param in self.possible_parameters.essential_params:
            param_name = param.name
            if param_name not in self.parameters:
                raise ValidationError(
                    f"Essential parameter missing from raw_params: {param}"
                )

    def _validate_if_unknown_params_supplied(self):
        """
        Checks if unknown parameter is supplied.

        Raises
        ------
        ValidationError
            When unknown parameter is supplied.
        """
        possible_params = [
            param.name
            for params in (
                self.possible_parameters.essential_params,
                self.possible_parameters.optional_params,
            )
            for param in params
        ]

        invalid_params = set(self.parameters.keys()) - set(possible_params)
        if invalid_params:
            raise ValidationError(
                f"Invalid parameters provided: {', '.join(invalid_params)}"
            )

    def _set_column_name(self):
        # if QATarget == Custom require target_column in raw_params

        if (
            "column_name" not in self.parameters.keys()
            or self.parameters["column_name"] == "standard"
            or self.parameters["column_name"] == "default"
        ):
            self.parameters["column_name"] = self.target.value

    def _neutron_checks(self):

        pass

    def _create_n0_lambda(self, method: QAMethod, params: dict):
        """
        Creates appropriate lambda function for N0-based checks using
        supplied parameters.

        Parameters
        ----------
        method : QAMethod
            The quality assessment method being used
        params : dict
            Dictionary containing the required parameters for lambda
            creation

        Returns
        -------
        Callable
            A lambda function configured with the supplied parameters
        """
        if method == QAMethod.ABOVE_N0:
            if "N0" not in params or "percent_maximum" not in params:
                raise ValueError(
                    "N0 and percent_maximum required for ABOVE_N0 check"
                )
            N0 = params["N0"]
            percent_maximum = params["percent_maximum"]
            return lambda x: x > (N0 * percent_maximum)

        elif method == QAMethod.BELOW_N0_FACTOR:
            if "N0" not in params or "percent_minimum" not in params:
                raise ValueError(
                    "N0 and percent_minimum required for BELOW_N0_FACTOR check"
                )
            N0 = params["N0"]
            percent_minimum = params["percent_minimum"]
            return lambda x: x < (N0 * percent_minimum)

        else:
            raise ValueError(
                f"Method {method} does not use N0 lambda functions"
            )

    def apply(self):
        saqc_method = getattr(SaQC, self.method.value[0])
        if self.method.value == "flagGeneric":  # special case
            if self.method in [QAMethod.ABOVE_N0, QAMethod.BELOW_N0_FACTOR]:
                func = self._create_n0_lambda(self.method, self.param_dict)
                return SaQC.flagGeneric(
                    field=self.param_dict["column_name"], func=func
                )
        return saqc_method(**self.param_set)


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
