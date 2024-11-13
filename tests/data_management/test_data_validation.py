import pandas as pd
from pandera.errors import SchemaError
import pytest

from neptoon.quality_control.data_validation_tables import (
    RawDataSchemaAfterFirstQA,
)


def test_relative_humidity_check():
    """
    Checks if the check on relative humidity is working as expected. It
    should raise an error if the RH values are in decimal format.
    """

    df_invalid = pd.DataFrame(
        {
            "moderated_count": [2000, 2010, 2001, 1980, 1999],
            "atmos_pressure": [990, 1000, 999, 956, 1110],
            # "relative_humidity": [25, 27, 13, 14, 15],
            "air_relative_humidity": [0.2, 0.3, 0.3, 0.4, 0.5],
            "date_time": ["2001", "2001", "2001", "2001", "2001"],
            "air_temperature": [10, 10, 10, 10, 10],
        }
    )

    with pytest.raises(SchemaError):
        RawDataSchemaAfterFirstQA.validate(df_invalid)
