from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, Any, Set, Type
from neptoon.columns import ColumnInfo


class QAMethod(Enum):
    """
    The methods that can be selected in neptoon. Methods are implemented
    using SaQC.

    For methods that use the same underlying SaQC function but with different
    configurations (like ABOVE_N0 and BELOW_N0_FACTOR both using flagGeneric),
    we use a tuple to store both the SaQC method and a discriminator.
    """

    RANGE_CHECK = ("flagRange", None)
    SPIKE_UNILOF = ("flagUniLOF", None)
    CONSTANT = ("flagConstants", None)
    ABOVE_N0 = ("flagRange", "above_n0")
    BELOW_N0_FACTOR = ("flagRange", "below_n0")

    @property
    def saqc_method(self) -> str:
        """Returns the underlying SaQC method name."""
        return self.value[0]

    @property
    def variant(self) -> str:
        """Returns the variant discriminator if any."""
        return self.value[1]


class QATarget(Enum):
    """
    The target data for the quality assessment selection.
    """

    RAW_EPI_NEUTRONS = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL)
    CORRECTED_EPI_NEUTRONS = str(
        ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
    )
    RELATIVE_HUMIDITY = str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY)
    AIR_PRESSURE = str(ColumnInfo.Name.AIR_PRESSURE)
    TEMPERATURE = str(ColumnInfo.Name.AIR_TEMPERATURE)
    SOIL_MOISTURE_VOL = str(ColumnInfo.Name.SOIL_MOISTURE_VOL_FINAL)
    CUSTOM = "custom"


@dataclass(frozen=True)
class ParameterSpec:
    """
    Specification for a single parameter.

    Attributes
    ----------
    name : str
        Parameter name
    description : str
        Parameter description
    units : Optional[str]
        Parameter units (if applicable)
    default : Any
        Default value (if optional)
    """

    name: str
    description: str
    optional: bool = False
    units: Optional[str] = None
    default: Any = None
    saqc_name: str = None


class MethodParameters:
    """
    Base class for method parameter specifications.
    Subclasses define parameter requirements for each method.
    """

    saqc_web: str = None
    essential_params: Set[ParameterSpec] = set()
    optional_params: Set[ParameterSpec] = set()


class AboveN0Parameters(MethodParameters):

    saqc_web = "https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html#saqc.SaQC.flagGeneric"

    essential_params: Set[ParameterSpec] = {
        ParameterSpec(
            name="N0",
            description="The N0 calibration number",
            units="neutron counts per hour",
            saqc_name="N0",
        ),
        ParameterSpec(
            name="percent_maximum",
            description="Fraction above N0 to flag. Commonly set to 1.075",
            units="decimal",
            saqc_name="percent_maximum",
        ),
    }


class BelowFactorofN0Parameters(MethodParameters):
    """Parameter specifications for below N0 factor check method."""

    saqc_web = "https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html#saqc.SaQC.flagGeneric"

    essential_params: Set[ParameterSpec] = {
        ParameterSpec(
            name="N0",
            description="The N0 calibration number",
            units="neutron counts per hour",
            saqc_name="N0",
        ),
        ParameterSpec(
            name="percent_minimum",
            description="The fraction of N0 below which to flag",
            units="decimal",
            saqc_name="percent_minimum",
        ),
    }


class RangeCheckParameters(MethodParameters):
    """Parameter specifications for range check method."""

    saqc_web = "https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html#saqc.SaQC.flagRange"

    essential_params = {
        ParameterSpec(
            name="min",
            description="Minimum acceptable value",
            units="data units",
            saqc_name="min",
        ),
        ParameterSpec(
            name="max",
            description="Maximum acceptable value",
            units="data units",
            saqc_name="max",
        ),
    }


class UniLOFParameters(MethodParameters):
    """Parameter specifications for range check method."""

    saqc_web = "https://rdm-software.pages.ufz.de/saqc/_api/saqc.SaQC.html#saqc.SaQC.flagUniLOF"

    essential_params = {}

    optional_params = {
        ParameterSpec(
            name="periods_in_calculation",
            description=str(
                "Number of periods to be included into the LOF calculation"
            ),
            units="time steps",
            default="20",
            saqc_name="n",
        ),
        ParameterSpec(
            name="threshold",
            description="Threshold for flagging",
            units="decimal",
            default="1.5",
            saqc_name="thresh",
        ),
        ParameterSpec(
            name="algorithm",
            description=(
                "Algorithm used for calculating the n-nearest "
                "neighbors needed for LOF calculation.\n"
                "    ['ball_tree', 'kd_tree', 'brute', 'auto']"
            ),
            units="Literal",
            default="ball_tree",
            saqc_name="algorithm",
        ),
    }


class WhatParamsDoINeed:
    """
    Helper class for discovering parameter requirements for QA methods.

    Parameters
    ----------
    method : SaQCMethodMap
        The quality assessment method to investigate

    Example
    -------
    >>> from neptoon.quality_control import WhatParamsDoINeed, QAMethod
    >>>
    >>> WhatParamsDoINeed(QAMethod.RANGE_CHECK)

    """

    def __init__(self, method: QAMethod):
        self.method = method
        self._param_class = ParameterRegistry.get_parameter_class(method)
        self.show_all_params()

    def show_required_params(self):
        """
        Display essential parameters for the method.
        """
        print(f"\nRequired parameters for {self.method}:")
        print("-" * 50)
        for param in self._param_class.essential_params:
            units_str = f"[{param.units}]" if param.units else ""
            print(f"{param.name} - {units_str}:")
            print(f"    {param.description}")

    def show_optional_params(self):
        """
        Display optional parameters for the method.
        """
        print(f"\nOptional parameters for {self.method}:")
        print("-" * 50)
        for param in self._param_class.optional_params:
            units_str = f"[{param.units}]" if param.units else ""
            default_str = f" (default: {param.default})"
            print(f"{param.name} - {units_str}{default_str}:")
            print(f"    {param.description}")

    def show_link_to_site(self):
        """
        Adds a link to the SaQC documentation
        """
        print(f"\nFurther information about {self.method}:")
        print("-" * 50)
        print(self._param_class.saqc_web)

    def show_all_params(self):
        """
        Display the params for the method.
        """
        self.show_required_params()
        self.show_optional_params()
        self.show_link_to_site()


class ParameterRegistry:
    """
    Central registry for mapping quality assessment methods to their
    parameter types.

    This class manages the relationships between methods and their
    parameter specifications, providing type safety and validation.
    """

    _registry: Dict[QAMethod, Type[MethodParameters]] = {
        QAMethod.RANGE_CHECK: RangeCheckParameters,
        QAMethod.ABOVE_N0: AboveN0Parameters,
        QAMethod.BELOW_N0_FACTOR: BelowFactorofN0Parameters,
        QAMethod.SPIKE_UNILOF: UniLOFParameters,
    }

    @classmethod
    def get_parameter_class(cls, method: QAMethod):
        """
        Get the parameter class for a given method.

        Parameters
        ----------
        method : SaQCMethodMap
            The quality assessment method

        Returns
        -------
        Type[BaseParameters]
            The corresponding parameter class

        Raises
        ------
        KeyError
            If the method is not registered
        """
        if method not in cls._registry:
            raise KeyError(
                f"No parameter specification found for method {method}"
            )
        return cls._registry[method]


class QAConfigRegistry:
    """
    Registry system for mapping strings as found in the configuration
    file to specific QATarget and QAMethods.
    """

    _target_mapping = {
        "raw_neutrons": QATarget.RAW_EPI_NEUTRONS,
        "corrected_neutrons": QATarget.CORRECTED_EPI_NEUTRONS,
        "air_relative_humidity": QATarget.RELATIVE_HUMIDITY,
        "air_pressure": QATarget.AIR_PRESSURE,
        "temperature": QATarget.TEMPERATURE,
        "soil_moisture": QATarget.SOIL_MOISTURE_VOL,
    }

    _method_mapping = {
        "flag_range": QAMethod.RANGE_CHECK,
        "spike_uni_lof": QAMethod.SPIKE_UNILOF,
        "constant": QAMethod.CONSTANT,
        "greater_than_N0": QAMethod.ABOVE_N0,
        "below_N0_factor": QAMethod.BELOW_N0_FACTOR,
    }

    @classmethod
    def get_target(cls, target: str) -> QATarget:
        return cls._target_mapping[target]

    @classmethod
    def get_method(cls, method: str) -> QAMethod:
        return cls._method_mapping[method]
