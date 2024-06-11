import pytest
import pandas as pd
from neptoon.quality_assesment.quality_assesment import (
    DateTimeIndexValidator,
)


def test_date_time_index_validator():
    """
    Tests the object which checks if a DataFrame has a datetime index.
    """
    data = {
        "Column1": [1, 2, 3, 4, 5],
        "Column2": ["A", "B", "C", "D", "E"],
        "Column3": [10.1, 20.2, 30.3, 40.4, 50.5],
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValueError):
        DateTimeIndexValidator(df)


def test_date_time_index_validator_with_date():
    """
    Tests the object which checks if a DataFrame has a datetime index.
    """
    data = {
        "Column1": [1, 2, 3, 4, 5],
        "Column2": ["A", "B", "C", "D", "E"],
        "Column3": [10.1, 20.2, 30.3, 40.4, 50.5],
    }
    df = pd.DataFrame(data)
    date_range = pd.date_range(start="2023-01-01", periods=5, freq="D")
    df.index = date_range
    DateTimeIndexValidator(df)
