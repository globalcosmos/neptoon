import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def data_to_smooth_hourly():
    return pd.Series(
        np.random.randn(100),
        index=pd.date_range(start="2023-01-01", periods=100, freq="h"),
    )


temp_test_data = pd.Series(
    np.random.randn(100),
    index=pd.date_range(start="2023-01-01", periods=100, freq="h"),
)


def test_smooth_data(data_to_smooth_hourly):
    data_to_smooth_hourly = temp_test_data
    smoothed_data = pd.Series(data=data_to_smooth_hourly)
    smoothed_data = smoothed_data.rolling(window=12, center=False).mean()
    assert len(smoothed_data) == len(data_to_smooth_hourly)


test_smooth_data(temp_test_data)


# test validation steps of Smoother
