from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pathlib import Path
from datetime import datetime
import yaml

from neptoon.logging import get_logger
from enum import Enum


core_logger = get_logger()


class BaseConfig(BaseModel):
    """
    Base configuration class with flexible field allowance.
    All configuration models inherit from this to maintain consistency.
    """

    model_config = ConfigDict(
        extra="allow",
        frozen=False,
    )


# Site Metadata Validation


class SensorInfo(BaseConfig):
    """General site metadata section."""

    name: str = Field(
        description="The name of the site.",
        examples=["Sheepdrove", "Gatton"],
    )
    country: str = Field(
        description="The country the site is located in.",
        examples=["DEU", "UK", "USA", "KOR"],
    )
    identifier: str = Field(
        description="A unique identier",
        examples=["101", "456"],
    )
    install_date: datetime
    latitude: float
    longitude: float
    elevation: float
    time_zone: int
    site_cutoff_rigidity: float
    avg_lattice_water: Optional[float] = Field(default=None)
    avg_soil_organic_carbon: Optional[float] = Field(default=None)
    avg_dry_soil_bulk_density: Optional[float] = Field(default=None)
    N0: Optional[int] = Field(
        gt=0, description="The N0 calibration term.", default=None
    )
    beta_coefficient: Optional[float] = Field(default=None)
    mean_pressure: Optional[float] = Field(default=None)


# Time Series Validation


class TimeSeriesColumns(BaseConfig):
    """
    Defines the structure for column configurations while allowing
    extensions.
    """

    epithermal_neutron_columns: List[str]
    thermal_neutron_columns: Optional[List[str]] = None
    neutron_count_units: Literal[
        "absolute_count", "counts_per_hour", "counts_per_second"
    ]
    pressure_columns: List[str]
    pressure_units: Optional[str] = None
    pressure_merge_method: Optional[Literal["priority", "average"]] = (
        "priority"
    )
    temperature_columns: List[str]
    temperature_merge_method: Optional[Literal["priority", "average"]] = (
        "priority"
    )
    relative_humidity_columns: List[str]
    relative_humidity_units: Optional[str] = None
    relative_humidity_merge_method: Optional[
        Literal["priority", "average"]
    ] = "priority"
    date_time_columns: List[str]
    date_time_format: str


class Temporal(BaseConfig):
    input_resolution: str = Field(default="1hour")
    output_resolution: str = Field(default=None)
    align_timestamps: bool = Field(default=False)
    alignment_method: str | None = Field(default="time")
    aggregate_method: str | None = Field(default="bagg")
    aggregate_func: str | None = Field(default="mean")
    aggregate_maxna_fraction: float | None = Field(default=0.5)


class TimeSeriesData(BaseConfig):
    path_to_data: Optional[str] = Field(default=None)
    temporal: Optional[Temporal] = None
    key_column_info: Optional[TimeSeriesColumns] = None


# Parser Validation


class ParserKeywords(BaseModel):
    """Configuration for specific parser keywords."""

    strip_left: bool = Field(default=True, description="TODO")
    digit_first: bool = Field(
        default=True,
        description="TODO",
    )


class RawDataParseConfig(BaseModel):
    """Configuration for parsing raw data files."""

    parse_raw_data: bool = Field(
        default=True, description="Whether to parse raw data files"
    )

    data_location: Optional[Path] = Field(
        description="Path to the raw data files or directory"
    )

    column_names: Optional[List[str]] = Field(
        default=None,
        description="A list of the raw column names in the order they appear",
    )

    prefix: Optional[str] = Field(
        default="",
        description="Prefix of file name for file filtering",
    )

    suffix: Optional[str] = Field(
        default="",
        description="Suffix of file name used for file filtering",
    )

    encoding: Optional[str] = Field(
        default="cp850",
        description="File encoding format",
    )

    skip_lines: Optional[int] = Field(
        default=0,
        description="Number of lines to skip at start of file",
    )

    separator: Optional[str] = Field(
        default=",",
        description="Column separator character",
    )

    decimal: Optional[str] = Field(
        default=".",
        description="Decimal point character",
    )

    skip_initial_space: Optional[bool] = Field(
        default=True,
        description="Whether to skip initial whitespace when making dataframe",
    )

    parser_kw: Optional[ParserKeywords] = Field(
        default_factory=ParserKeywords,
        description="Additional parser-specific keywords",
    )

    starts_with: Optional[str] = Field(
        default="",
        description="String that headers must start with when parsing",
    )

    multi_header: Optional[bool] = Field(
        default=False,
        description="Whether to expect multi-line headers",
    )

    strip_names: Optional[bool] = Field(
        default=True,
        description="Whether to strip whitespace from column names",
    )

    remove_prefix: Optional[str] = Field(
        default="//",
        description="Prefix to remove from column names",
    )


# QA Validation


class FlagRange(BaseConfig):
    """Common pattern for min/max range checks."""

    min: Optional[float] = Field(
        default=float("-inf"),
        description="minimum value below which data is removed",
    )
    max: Optional[float] = Field(
        default=float("inf"),
        description="maximum value below which data is removed",
    )

    @model_validator(mode="after")
    def validate_range(cls, values):
        """Validate min is less than max after both fields are set."""
        min_val = values.min if values.min is not None else float("-inf")
        max_val = values.max if values.max is not None else float("inf")

        if min_val > max_val:
            raise ValueError(
                f"min value ({min_val}) must be less than max value ({max_val})"
            )

        return values


class PersistenceCheck(BaseConfig):
    """Configuration for persistence checking."""

    threshold: Optional[float] = None
    window: Optional[int] = None
    min_periods: Optional[int] = None


class SpikeUniLOF(BaseConfig):

    periods_in_calculation: Optional[int] = 20
    threshold: Optional[float] = 1.5
    algorithm: Optional[Literal["ball_tree", "kd_tree", "brute", "auto"]] = (
        Field(default="ball_tree")
    )


class GreaterThanN0(BaseConfig):

    percent_maximum: float = Field(
        default=1.075,
        description="The factor above N0 to flag values",
    )


class BelowN0Factor(BaseConfig):

    percent_minimum: float = Field(
        default=0.3,
        description=(
            "The proportion of N0 value below " "which neutrons are flagged"
        ),
    )


class QAColumnConfig(BaseConfig):
    """
    Base configuration for QA columns.

    Includes all possible QA systems as optional.
    """

    flag_range: Optional[FlagRange] = None
    persistance_check: Optional[PersistenceCheck] = None
    spike_uni_lof: Optional[SpikeUniLOF] = None
    greater_than_N0: Optional[GreaterThanN0] = None
    below_N0_factor: Optional[BelowN0Factor] = None


class QAConfig(BaseConfig):
    """Quality assessment configuration section."""

    air_humidity: Optional[QAColumnConfig] = None
    air_pressure: Optional[QAColumnConfig] = None
    temperature: Optional[QAColumnConfig] = None
    soil_moisture: Optional[QAColumnConfig] = None


class SoilMoistureQA(BaseConfig):
    soil_moisture: Optional[QAColumnConfig] = None


# Calibration Validation


class CalibrationColumnNames(BaseConfig):
    """Column naming configuration for calibration data."""

    date_time: str = Field(default="date_time")
    profile_id: str = Field(default="profile_id")
    sample_depth: str = Field(default="sample_depth")
    radial_distance_from_sensor: str = Field(
        default="radial_distance_from_sensor"
    )
    bulk_density_of_sample: str = Field(default="bulk_density_of_sample")
    gravimetric_soil_moisture: str = Field(
        default="soil_moisture_gravimetric_column"
    )
    soil_organic_carbon: str = Field(default="soil_organic_carbon")
    lattice_water: str = Field(default="lattice_water")


class CalibrationConfig(BaseConfig):
    """Configuration for calibration data."""

    calibrate: bool = Field(default=False)

    data_format: Optional[
        Literal["custom", "cosmoz", "cosmos-usa", "cosmos-uk"]
    ] = Field(default="custom")
    location: Optional[Path] = Field(default="")
    key_column_names: Optional[CalibrationColumnNames] = None


class DataStorageConfig(BaseConfig):
    save_folder: Optional[str] = Field(default=None)
    append_timestamp_to_folder_name: Optional[bool] = Field(default=True)
    append_audit_log_hash_to_folder_name: Optional[bool] = Field(default=False)
    create_report: Optional[bool] = Field(default=False)


class FiguresConfig(BaseConfig):
    create_figures: bool = Field(default=True)
    make_all_figures: bool = Field(default=True)
    custom_list: Optional[List[str]] = Field(
        default=None,
        description="A list of the figures to process",
    )


class SensorConfig(BaseConfig):
    """Top-level configuration."""

    sensor_info: SensorInfo
    time_series_data: Optional[TimeSeriesData] = None
    input_data_qa: Optional[QAConfig] = None
    soil_moisture_qa: Optional[SoilMoistureQA] = None
    raw_data_parse_options: Optional[RawDataParseConfig] = None
    calibration: Optional[CalibrationConfig] = None
    data_storage: Optional[DataStorageConfig] = None
    figures: Optional[FiguresConfig] = None


####################
## Process Config ##
####################


class NeutronQualityAssessment(BaseConfig):
    """Quality assessment configuration for Neutrons"""

    raw_neutrons: QAColumnConfig
    corrected_neutrons: QAColumnConfig


class ReferenceNeutronMonitor(BaseModel):
    """Configuration for reference neutron monitor settings."""

    station: str = Field(
        default="JUNG", description="Station identifier for neutron monitoring"
    )
    resolution: int = Field(
        default=60, description="Time resolution in minutes", ge=1
    )
    nmdb_table: str = Field(
        default="revori", description="NMDB table name to query"
    )


class AirHumidityCorrection(BaseModel):
    """Configuration for air humidity correction parameters."""

    method: Literal["rosolem_2013"] = Field(
        description="Air humidity correction method"
    )
    omega: float = Field(
        default=0.0054,
        description="Omega coefficient for humidity correction",
        gt=0,
    )
    humidity_ref: float = Field(
        default=0, description="Reference humidity value"
    )


class AirPressureCorrection(BaseModel):
    """Configuration for air pressure correction parameters."""

    method: Literal["zreda_2012"] = Field(
        description="Air pressure correction method"
    )
    dunai_inclination: Optional[float] = Field(
        default=None, description="Dunai inclination parameter"
    )


class SoilMoistureEstimation(BaseModel):
    """Configuration for the conversion of neutrons to soil moisture"""

    method: Literal["desilets_etal_2010", "koehli_etal_2021"] = Field(
        description="Soil moisture estimation theory",
        default="desilets_etal_2010",
    )
    koehli_method_form: Literal[
        "Jan23_uranos",
        "Jan23_mcnpfull",
        "Mar12_atmprof",
        "Mar21_mcnp_drf",
        "Mar21_mcnp_ewin",
        "Mar21_uranos_drf",
        "Mar21_uranos_ewin",
        "Mar22_mcnp_drf_Jan",
        "Mar22_mcnp_ewin_gd",
        "Mar22_uranos_drf_gd",
        "Mar22_uranos_ewin_chi2",
        "Mar22_uranos_drf_h200m",
        "Aug08_mcnp_drf",
        "Aug08_mcnp_ewin",
        "Aug12_uranos_drf",
        "Aug12_uranos_ewin",
        "Aug13_uranos_atmprof",
        "Aug13_uranos_atmprof2",
    ] = Field(
        description="Koehli specific method for converting neutrons",
        default="Mar21_uranos_drf",
    )


class IncomingRadiationCorrection(BaseModel):
    """Configuration for incoming radiation correction parameters."""

    method: Literal[
        "zreda_2012",
        "hawdon_2014",
        "mcjannet_desilets_2023",
    ] = Field(description="Incoming radiation correction method")

    reference_neutron_monitor: ReferenceNeutronMonitor = Field(
        default_factory=ReferenceNeutronMonitor,
        description="Reference neutron monitor configuration",
    )


class BiomassCorrection(BaseModel):
    """Configuration for above ground biomass correction parameters."""

    method: Optional[str] = Field(
        default=None, description="Above ground biomass correction method"
    )


class CorrectionSteps(BaseModel):
    """Main configuration for all correction steps."""

    air_humidity: Optional[AirHumidityCorrection] = Field(
        default=None, description="Air humidity correction configuration"
    )
    air_pressure: Optional[AirPressureCorrection] = Field(
        default=None, description="Air pressure correction configuration"
    )
    incoming_radiation: Optional[IncomingRadiationCorrection] = Field(
        default=None, description="Incoming radiation correction configuration"
    )
    above_ground_biomass: Optional[BiomassCorrection] = Field(
        default=None,
        description="Above ground biomass correction configuration",
    )
    soil_moisture_estimation: Optional[SoilMoistureEstimation] = Field(
        default=None, description="Soil Moisture estimation configuration"
    )


class SmoothingAlgorithmSettings(BaseModel):
    """
    Configuration settings for data smoothing algorithms.

    Validates and enforces constraints specific to different smoothing methods:
    - Window size must be positive
    - For Savitzky-Golay:
        - Window size should be odd
        - Polynomial order must be less than window size
    """

    algorithm: Literal["savitsky_golay", "rolling_mean"] = Field(
        default="savitsky_golay", description="Smoothing algorithm to apply"
    )
    window: str = Field(
        default="12h", description="Temporal size of window for smoothing"
    )
    poly_order: Optional[int] = Field(
        default=4,
        description="Polynomial order for Savitzky_Golay filter",
        ge=0,
    )

    @model_validator(mode="after")
    def validate_poly_order(self) -> "SmoothingAlgorithmSettings":
        """Validate polynomial order relative to window size."""
        if self.algorithm == "savitsky_golay":
            if self.poly_order >= self.window:
                raise ValueError(
                    "Polynomial order must be less than window size "
                    f"(got order={self.poly_order}, window={self.window})"
                )
        return self


class DataSmoothingConfig(BaseModel):
    """
    Main configuration for data smoothing operations.

    Controls which data series should be smoothed and defines the
    smoothing parameters to be applied.
    """

    smooth_corrected_neutrons: bool = Field(
        default=True, description="Apply smoothing to corrected neutron counts"
    )
    smooth_soil_moisture: bool = Field(
        default=False,
        description="Apply smoothing to calculated soil moisture values",
    )
    settings: SmoothingAlgorithmSettings = Field(
        default_factory=SmoothingAlgorithmSettings,
        description="Smoothing algorithm configuration",
    )


class ProcessConfig(BaseConfig):

    neutron_quality_assessment: NeutronQualityAssessment
    correction_steps: CorrectionSteps
    data_smoothing: DataSmoothingConfig


class ConfigType(Enum):
    SENSOR = "sensor"
    PROCESS = "process"


class ConfigurationManager:
    """Manages loading and access of nested configurations."""

    def __init__(self):
        self._configs: Dict[str, BaseConfig] = {}

    def _get_working_directory(
        self,
        config_dict: dict,
        config_path: Path,
    ):
        if "working_directory" in config_dict and isinstance(
            config_dict["working_directory"], str
        ):
            parent_path = Path(config_dict["working_directory"])
        else:
            parent_path = config_path.parent
        return parent_path

    def _resolve_paths(
        self,
        config_dict: dict,
        config_path: Path,
        parent_path: Optional[Path] = None,
    ):
        """
        Resolves the paths in the YAML file so that any relative paths
        are relative to the config file itself. The given paths are
        resolved to Path objects.

        Parameters
        ----------
        config_dict : dict
            The loaded YAML file as a dict
        config_path : Path
            The Path of the config YAML

        Returns
        -------
        dict
            Dictionary with paths as Path objects.
        """
        if parent_path is None:
            parent_path = self._get_working_directory(
                config_dict=config_dict, config_path=config_path
            )

        resolved_dict = {}
        for key, value in config_dict.items():
            if isinstance(value, dict):
                resolved_dict[key] = self._resolve_paths(
                    value,
                    config_path=config_path,
                    parent_path=parent_path,
                )
            elif isinstance(value, str) and (
                "path_" in key.lower() or "location" in key.lower()
            ):
                path = Path(value)
                if not path.is_absolute():
                    path = (parent_path / path).resolve()

                resolved_dict[key] = str(path)
            else:
                resolved_dict[key] = value
        return resolved_dict

    def load_configuration(self, file_path: str) -> None:
        """
        Load and validate nested configuration.

        Parameters
        ----------
        file_path : str
            Path to YAML configuration file
        """

        config_path = Path(file_path).resolve()

        with open(file_path) as f:
            config_dict = yaml.safe_load(f)
        config_dict = self._resolve_paths(config_dict, config_path)

        if config_dict["config"] == "sensor":
            config_type = str(ConfigType.SENSOR.value)
            self._configs[config_type] = SensorConfig(**config_dict)
        elif config_dict["config"] == "process":
            config_type = str(ConfigType.PROCESS.value)
            self._configs[config_type] = ProcessConfig(**config_dict)

    def get_config(self, name: Literal["sensor", "process"]):
        """
        Return the specific config

        Parameters
        ----------
        name : str
            Either sensor or process

        Returns
        -------
        BaseConfig
            The requested config
        """
        return self._configs[name]

    def create_sensor_config(self):
        pass
