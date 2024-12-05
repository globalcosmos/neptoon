from typing import List, Optional, Literal, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pathlib import Path
from datetime import datetime
from neptoon.logging import get_logger


core_logger = get_logger()

## Changes tracker TODO
"""
def TrackChanges:
    # when change of value occurs, store old and new value + timestamp

Add to ConfigManager
"""


class BaseConfig(BaseModel):
    """
    Base configuration class with flexible field allowance.
    All configuration models inherit from this to maintain consistency.
    """

    model_config = ConfigDict(
        extra="allow",
        frozen=False,
    )


class GeneralSiteMetaData(BaseConfig):
    """General site metadata section."""

    site_name: str = Field(
        description="The name of the site.",
        examples=["Sheepdrove", "Gatton"],
    )
    site_country: str = Field(
        description="The country the site is located in.",
        examples=["DEU", "UK", "USA", "KOR"],
    )
    site_identifier: str = Field(
        description="A unique identier",
        examples=["101", "456"],
    )
    install_date: datetime
    latitude: float
    longitude: float
    elevation: float
    time_zone: int
    site_cutoff_rigidity: float
    reference_incoming_neutron_value: float
    avg_lattice_water: Optional[float]
    avg_soil_organic_carbon: Optional[float]
    avg_dry_soil_bulk_density: Optional[float]
    N0: Optional[int] = Field(gt=0, description="The N0 calibration term.")
    beta_coefficient: Optional[float]
    l_coefficient: Optional[float]
    mean_pressure: Optional[float]
    avg_precipitation: Optional[float]
    avg_soil_moisture: Optional[float]
    avg_biomass: Optional[float]


class TimeSeriesColumns(BaseConfig):
    """
    Defines the structure for column configurations while allowing
    extensions.
    """

    epithermal_neutron_counts_columns: List[str]
    thermal_neutrons: Optional[List[str]] = None
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
    relative_humidity_units: Optional[str]
    relative_humidity_merge_method: Optional[
        Literal["priority", "average"]
    ] = "priority"
    date_time_columns: List[str]


class TimeSeriesData(BaseConfig):
    time_step_resolution: str
    date_time_format: str
    initial_time_zone: Optional[str] = None
    convert_time_zone_to: Optional[str] = None
    key_column_info: TimeSeriesColumns


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

    data_location: Path = Field(
        description="Path to the raw data files or directory"
    )

    column_names: Optional[List[str]] = Field(
        default=None,
        description="A list of the raw column names in the order they appear",
    )

    prefix: str = Field(
        default="",
        description="Prefix of file name for file filtering",
    )

    suffix: str = Field(
        default="",
        description="Suffix of file name used for file filtering",
    )

    encoding: str = Field(
        default="cp850",
        description="File encoding format",
    )

    skip_lines: int = Field(
        default=0,
        description="Number of lines to skip at start of file",
    )

    separator: str = Field(
        default=",",
        description="Column separator character",
    )

    decimal: str = Field(
        default=".",
        description="Decimal point character",
    )

    skip_initial_space: bool = Field(
        default=True,
        description="Whether to skip initial whitespace when making dataframe",
    )

    parser_kw: ParserKeywords = Field(
        default_factory=ParserKeywords,
        description="Additional parser-specific keywords",
    )

    starts_with: str = Field(
        default="",
        description="String that headers must start with when parsing",
    )

    multi_header: bool = Field(
        default=False,
        description="Whether to expect multi-line headers",
    )

    strip_names: bool = Field(
        default=True,
        description="Whether to strip whitespace from column names",
    )

    remove_prefix: str = Field(
        default="//",
        description="Prefix to remove from column names",
    )

    def model_post_init(
        self,
    ) -> None:
        """Validate path exists if parse_raw_data is True."""
        if self.parse_raw_data and not self.data_location.exists():
            raise ValueError(
                f"Data location does not exist: {self.data_location}"
            )


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
    algorithm: Optional[Literal["ball_tree", "kd_tree", "brute", "auto"]]


class QAColumnConfig(BaseConfig):
    """
    Base configuration for QA columns.

    Includes all possible QA systems as optional.
    """

    flag_range: Optional[FlagRange] = None
    persistance_check: Optional[PersistenceCheck] = None
    spike_uni_lof: Optional[SpikeUniLOF] = None


class QAConfig(BaseConfig):
    """Quality assessment configuration section."""

    air_humidity: Optional[QAColumnConfig] = None
    air_pressure: Optional[QAColumnConfig] = None
    temperature: Optional[QAColumnConfig] = None


class CalibrationColumnNames(BaseConfig):
    """Column naming configuration for calibration data."""

    profile: str = Field(default="PROF")
    sample_depth: str = Field(default="DEPTH_AVG")
    radial_distance_from_sensor: str = Field(default="LOC_rad")


class CalibrationConfig(BaseConfig):
    """Configuration for calibration data."""

    format: Literal["neptoon", "cosmoz", "cosmos-usa", "cosmos-uk"]
    location: Optional[Path] = None
    key_column_names: CalibrationColumnNames


class StationConfig(BaseConfig):
    """Top-level configuration."""

    general_site_metadata: GeneralSiteMetaData
    input_data_qa: Optional[QAConfig] = None
    calibration_data: CalibrationConfig


class ConfigurationManager:
    """Manages loading and access of nested configurations."""

    def __init__(self):
        self._config: Optional[StationConfig] = None

    def load_configuration(self, file_path: str) -> None:
        """
        Load and validate deeply nested configuration.

        Parameters
        ----------
        file_path : str
            Path to YAML configuration file
        """
        import yaml

        with open(file_path) as f:
            config_dict = yaml.safe_load(f)

        self._config = StationConfig(**config_dict)

    @property
    def config(self) -> StationConfig | str:
        """
        Access the validated configuration.

        Returns
        -------
        MainConfig
            The complete configuration object

        Raises
        ------
        ValueError
            If configuration hasn't been loaded
        """
        if self._config is None:
            raise ValueError("Configuration not loaded")
        return self._config
