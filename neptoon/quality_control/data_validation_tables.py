import pandera.pandas as pa
from pandera.typing import Series, DataFrame  # Index
from typing import Optional


class FormatCheck(pa.DataFrameModel):
    """
    This is the validation table which is used to check that the time
    series data has been correctly formatted for use in cosmosbase.

    When data is read in it must either validate against this format, or
    it must be pre-formatted using another script into this format.

    This initial step checks the column names are as expected and that
    the data types are as expected.
    """

    # Essential Columns
    # pandera.Int is a nullable Integer type
    epithermal_neutrons_cph: float = pa.Field(nullable=True)
    air_pressure: float = pa.Field(nullable=True)
    air_relative_humidity: float = pa.Field(
        nullable=True,
    )
    air_temperature: float = pa.Field(nullable=True)

    # Optional columns
    precipitation: Optional[float] = pa.Field(nullable=True)
    snow_depth: Optional[float] = pa.Field(nullable=True)
    thermal_neutrons: Optional[float] = pa.Field(nullable=True)


class RawDataSchemaAfterFirstQA(FormatCheck):
    """
    This is an extension of the RawDataSchema to check data after the
    first formatting and validation steps.
    """

    epithermal_neutrons_cph: int = pa.Field(nullable=True, gt=0)
    air_pressure: float = pa.Field(gt=600)
    air_relative_humidity: float = pa.Field(
        nullable=True,
        ge=0,
        le=100,
    )

    incoming_neutron_intensity: float = pa.Field(nullable=True)

    @pa.check("air_relative_humidity")
    def relative_humidity_validation(cls, series: Series[float]) -> bool:
        """
        Check to ensure that relative humidity is given a percentage
        format (i.e., 20.0%) and not decimal format (i.e., 0.2). Ensures
        consistany when applying corrections.
        """

        decimal_like_values = series < 1
        if (
            decimal_like_values.mean() > 0.5
        ):  # More than 50% of values are below 1
            return False
        return True

    @pa.check()
    def check_date_time_removed_and_indexed(cls, df: DataFrame) -> bool:
        """
        Checks that the date_time column has been assigned to index and
        removed from the dataframe as a column.
        """
        return "date_time" not in df.columns
