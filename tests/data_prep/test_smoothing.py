import pandas as pd
import numpy as np
import pytest
from neptoon.data_prep.smoothing import SmoothData
from neptoon.columns.column_information import ColumnInfo


@pytest.fixture
def data_to_smooth_hourly():
    """
    Dataset used for tests
    """
    series1 = pd.Series(
        np.random.randn(100),
        index=pd.date_range(start="2023-01-01", periods=100, freq="h"),
        name=str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
    )
    df = pd.DataFrame(series1)
    df["corrected_epithermal_neutrons_uncertainty"] = np.random.randn(100)
    return df


@pytest.fixture
def data_to_smooth_hourly_bad_index():
    """
    Dataset used for tests with incorrect index type
    """
    series = pd.Series(
        np.random.randn(100),
        name=str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
    )
    return pd.DataFrame(series)


def test_smooth_data_rolling(data_to_smooth_hourly):
    """
    Tests to check smoothing using rolling mean occurs correctly.
    """
    smoother = SmoothData(
        data=data_to_smooth_hourly,
        column_to_smooth=str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
        smooth_method="rolling_mean",
        window="12h",
        auto_update_final_col=False,
    )
    smoothed_data = smoother.apply_smoothing()
    smoothed_col = smoother.create_new_column_name()
    assert len(smoothed_data) == len(data_to_smooth_hourly)
    assert smoothed_col == "epithermal_neutrons_cph_rollingmean_12h"
    assert smoothed_data[smoothed_col].isna().sum() == 7


def test_smooth_data_rolling_raise_error_int(data_to_smooth_hourly):
    """
    Tests to check smoothing using rolling mean occurs correctly.
    """
    with pytest.raises(ValueError):
        smoother = SmoothData(
            data=data_to_smooth_hourly,
            column_to_smooth="epithermal_neutrons",
            smooth_method="rolling_mean",
            window=12,
            auto_update_final_col=False,
        )


@pytest.mark.reset_columns
def test_update_col_name_final(data_to_smooth_hourly):
    """
    Test to check ColumnInfo is auto updated when turned on.
    """
    data_to_smooth_hourly.rename(
        {"epithermal_neutrons": "epithermal_neutrons_cph"}, inplace=True
    )
    smoother = SmoothData(
        data=data_to_smooth_hourly,
        column_to_smooth=str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
        smooth_method="rolling_mean",
        window="12h",
        auto_update_final_col=True,
    )
    smoother.apply_smoothing()  # should automate update of ColumnInfo
    smoothed_col = smoother.create_new_column_name()
    assert str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL) == smoothed_col


@pytest.mark.reset_columns
def test_update_col_name_final_error(data_to_smooth_hourly):
    """
    Test to check exception caught when autoupdate turned on for
    incorrect column.
    """
    smoother = SmoothData(
        data=data_to_smooth_hourly,
        column_to_smooth="unusable_name",
        smooth_method="rolling_mean",
        window="12h",
        auto_update_final_col=True,
    )
    with pytest.raises(ValueError):
        smoother.apply_smoothing()


def test_validation_of_attributes_savitsky_golay(data_to_smooth_hourly):
    """
    Validation of attributes test when requesting SG filter smoothing.
    """
    with pytest.raises(ValueError):
        SmoothData(
            data=data_to_smooth_hourly,
            column_to_smooth="epithermal_neutrons",
            smooth_method="bad",
            window="12h",
            # no poly entered
            auto_update_final_col=False,
        )


def test_validation_of_attributes_datetime_index(
    data_to_smooth_hourly_bad_index,
):
    """
    Test for validation when bad index supplied.
    """
    with pytest.raises(ValueError):
        SmoothData(
            data=data_to_smooth_hourly_bad_index,
            column_to_smooth="epithermal_neutrons",
            smooth_method="savitsky_golay",
            window="12h",
            # no poly entered
            auto_update_final_col=False,
        )


@pytest.fixture
def data_to_smooth_daily():
    """
    Dataset used for tests
    """
    series1 = pd.Series(
        np.random.randn(100),
        index=pd.date_range(start="2023-01-01", periods=100, freq="d"),
        name=str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
    )
    df = pd.DataFrame(series1)
    df["corrected_epithermal_neutrons_uncertainty"] = np.random.randn(100)
    return df


@pytest.mark.reset_columns
def test_smooth_window_mismatch(data_to_smooth_daily):
    message = (
        "The resolution of the data is not fine enough for the "
        "desired smoothing window. Choose a larger smoothing window."
    )
    with pytest.raises(ValueError, match=message):
        SmoothData(
            data=data_to_smooth_daily,
            column_to_smooth="epithermal_neutrons",
            smooth_method="savitsky_golay",
            window="12h",
            # no poly entered
            auto_update_final_col=False,
        )
