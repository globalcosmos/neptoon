import pandera
from pandera.typing import Series, DataFrame  # Index
from typing import Optional


class RawDataSchema(pandera.DataFrameModel):
    """
    This is the validation table which is used to check that the time
    series data has been correctly formatted for use in cosmosbase.

    When data is read in it must either validate against this format, or
    it must be pre-formatted using another script into this format.

    This initial step checks the column names are as expected and that
    the data types are as expected.
    """

    # Essential Columns
    moderated_count: int = pandera.Field(nullable=True, coerce=True)
    atmos_pressure: float = pandera.Field(coerce=True)
    relative_humidity: float = pandera.Field(
        nullable=True,
        coerce=True,
    )
    air_temperature: float = pandera.Field(nullable=True, coerce=True)

    # Optional columns
    precipitation: Optional[float] = pandera.Field(nullable=True, coerce=True)
    snow_depth: Optional[float] = pandera.Field(nullable=True, coerce=True)
    thermal_count: Optional[int] = pandera.Field(nullable=True, coerce=True)


class RawDataSchemaAfterFirstQA(RawDataSchema):
    """
    This is an extension of the RawDataSchema to check data after the
    first formatting and validation steps.
    """

    moderated_count: int = pandera.Field(nullable=True, gt=0, coerce=True)
    atmos_pressure: float = pandera.Field(gt=600, coerce=True)
    relative_humidity: float = pandera.Field(
        nullable=True,
        ge=0,
        le=100,
        coerce=True,
    )

    incoming_neutron_intensity: float = pandera.Field(
        nullable=True, coerce=True
    )

    @pandera.check("relative_humidity")
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

    @pandera.check()
    def check_date_time_removed_and_indexed(cls, df: DataFrame) -> bool:
        """
        Checks that the date_time column has been assigned to index and
        removed from the dataframe as a column.
        """
        return "date_time" not in df.columns
