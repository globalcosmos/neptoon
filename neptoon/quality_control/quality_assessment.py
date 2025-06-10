from saqc import SaQC
import pandas as pd
from neptoon.logging import get_logger
from neptoon.data_audit import log_key_step
from neptoon.quality_control.saqc_methods_and_params import (
    QAMethod,
    QATarget,
    ParameterRegistry,
)

# from neptoon.quality_control.saqc_methods_and_params import WhatParamsDoINeed


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
    Create a quality check that flags neutron intensity values outside
    the range 500-550:

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

    See neptoon.quality_control.WhatParamsDoINeed if you need help on
    allowable params.
    """

    @log_key_step("target", "method", "raw_params")
    def __init__(
        self,
        target: QATarget,
        method: QAMethod,
        parameters: dict = {},
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
        """
        Converts parameter names from neptoon style to saqc, ready for
        use.

        Parameters
        ----------
        parameters : dict
            Dictionary containing parameters

        Returns
        -------
        _type_
            _description_
        """
        # Get essential parameter conversions
        essential_params = getattr(
            self.possible_parameters, "essential_params", []
        )
        name_mapping_essential = {
            param.name: param.saqc_name for param in essential_params
        }
        converted_essential = {
            name_mapping_essential[param_name]: param_value
            for param_name, param_value in parameters.items()
            if param_name in name_mapping_essential
        }

        # Get optional parameter conversions
        optional_params = getattr(
            self.possible_parameters, "optional_params", []
        )
        name_mapping_optional = {
            param.name: param.saqc_name for param in optional_params
        }
        converted_optional = {
            name_mapping_optional[param_name]: param_value
            for param_name, param_value in parameters.items()
            if param_name in name_mapping_optional
        }

        # Combine both parameter sets
        converted_essential.update(converted_optional)
        converted_essential["field"] = parameters["column_name"]
        return converted_essential

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
        # TODO if QATarget == Custom require target_column in raw_params

        if (
            "column_name" not in self.parameters.keys()
            or self.parameters["column_name"] == "standard"
            or self.parameters["column_name"] == "default"
        ):
            self.parameters["column_name"] = self.target.value

    def _set_new_saqc_dict_for_n0(self):
        """
        Lambda funcs used for QA of corrected neutrons.

        Returns
        -------
        func
            returns the complete lambda func
        """
        if self.method == QAMethod.ABOVE_N0:
            field = self.saqc_param_dict["field"]
            max = (
                self.saqc_param_dict["N0"]
                * self.saqc_param_dict["percent_maximum"]
            )

            new_dict = {"field": field, "max": max}
        elif self.method == QAMethod.BELOW_N0_FACTOR:
            field = self.saqc_param_dict["field"]
            min = (
                self.saqc_param_dict["N0"]
                * self.saqc_param_dict["percent_minimum"]
            )
            new_dict = {"field": field, "min": min}

        self.saqc_param_dict = new_dict

    def apply(self, qc: SaQC):
        saqc_method = getattr(qc, self.method.value[0])
        if self.method in [QAMethod.ABOVE_N0, QAMethod.BELOW_N0_FACTOR]:
            self._set_new_saqc_dict_for_n0()
        return saqc_method(**self.saqc_param_dict)


class QualityAssessmentFlagBuilder:
    """
    Staging place for the checks as they are built. First a user adds a
    check using the add_check method.
    """

    def __init__(self):
        self.checks = []
        self._targets = []

    def add_check(self, *checks):
        for check in checks:
            if isinstance(check, QualityCheck):
                self.checks.append(check)
        return self

    def apply_checks(self, qc):
        for check in self.checks:
            qc = check.apply(qc)
            self._targets.append(check.target)
        return qc

    def return_targets(self):
        return self._targets


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
        saqc: SaQC | None = None,
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

    def return_flags_data_frame(
        self,
        current_flag_data_frame: pd.DataFrame | None = None,
    ):
        """
        Returns the flag dataframe

        Returns
        -------
        pd.DataFrame
            The DataFrame with assigned flags
        """
        if current_flag_data_frame is None:
            return self.qc.flags.to_pandas()
        else:
            new_flags = self.qc.flags.to_pandas()
            new_targets = self.builder.return_targets()

            for target in new_targets:
                col_name = target.value
                current_flag_data_frame[col_name] = new_flags[col_name]
            return current_flag_data_frame
