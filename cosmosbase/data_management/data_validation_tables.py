import pandas as pd
import pandera
from pandera.typing import Series  # Index

df = pd.DataFrame(
    {
        "moderated_count": [2000, 2010, 2001, 1980, 1999],
        "atmos_pressure": [990, 1000, 999, 956, 1110],
        # "relative_humidity": [25, 27, 13, 14, 15],
        "relative_humidity": [0.2, 0.3, 0.3, 0.4, 0.5],
        "date_time": ["2001", "2001", "2001", "2001", "2001"],
    }
)


class RawDataSchema(pandera.DataFrameModel):
    """
    This is the validation table which is used to check that the time
    series data has been correctly formatted for use in cosmosbase. The
    concept is that when data is read in it must either be in this
    format, or it must be pre-formatted using another script into this
    format. The exact rules may change with time. When changes are made
    on the data it will always be validated by one of these
    pandera.DataFrameModels to ensure it has been converted correctly.
    """

    moderated_count: int = pandera.Field(nullable=True, coerce=True)
    atmos_pressure: float = pandera.Field(coerce=True)
    relative_humidity: float = pandera.Field(
        nullable=True,
        coerce=True,
    )


class RawDataSchemaAfterFirstQA(RawDataSchema):
    """
    This is an extension of the RawDataSchema to check data after the
    first formatting and validation steps
    """

    moderated_count: int = pandera.Field(nullable=True, gt=0, coerce=True)
    atmos_pressure: float = pandera.Field(gt=600, coerce=True)
    relative_humidity: float = pandera.Field(
        nullable=True,
        ge=0,
        le=100,
        coerce=True,
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


RawDataSchema(df)
