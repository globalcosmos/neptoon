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
    return pd.Series(
        np.random.randn(100),
        index=pd.date_range(start="2023-01-01", periods=100, freq="h"),
        name="epithermal_neutrons",
    )


@pytest.fixture
def data_to_smooth_hourly_bad_index():
    """
    Dataset used for tests with incorrect index type
    """
    return pd.Series(
        np.random.randn(100),
        name="epithermal_neutrons",
    )


@pytest.fixture()
def reset_column_info():
    """
    Automatically resets ColumnInfo labels before runnning test.
    Important for tests related to ColumnInfo renaming.
    """
    ColumnInfo.reset_labels()
    yield
    ColumnInfo.reset_labels()


# Marker for tests that change ColumnInfo
pytest.mark.reset_columns = pytest.mark.usefixtures("reset_column_info")


@pytest.fixture
def og_data_table():
    """
    Data table for tests to ensure appending works correctly.
    """
    return pd.DataFrame(
        index=pd.date_range(start="2023-01-01", periods=100, freq="h"),
        columns=["epithermal_neutrons", "air_pressure", "temperature"],
    )


def test_smooth_data_rolling(data_to_smooth_hourly, og_data_table):
    """
    Tests to check smoothing using rolling mean occurs correctly.
    """
    smoother = SmoothData(
        data=data_to_smooth_hourly,
        column_to_smooth="epithermal_neutrons",
        smooth_method="rolling_mean",
        window="12h",
        auto_update_final_col=False,
    )
    smoothed_data = smoother.apply_smoothing()
    smoothed_col = smoother.create_new_column_name()
    assert len(smoothed_data) == len(data_to_smooth_hourly)
    assert smoothed_data.isna().sum() == 5
    assert smoothed_col == "epithermal_neutrons_rollingmean_12h"
    og_data_table[smoothed_col] = smoothed_data
    assert smoothed_col in og_data_table.columns


def test_smooth_data_rolling_raise_error_int(
    data_to_smooth_hourly, og_data_table
):
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


# def test_smooth_data_savitsky_golay(data_to_smooth_hourly, og_data_table):
#     """
#     Tests to check smoothing using savitsky golay occurs correctly.
#     """
#     smoother = SmoothData(
#         data=data_to_smooth_hourly,
#         column_to_smooth="epithermal_neutrons",
#         smooth_method="savitsky_golay",
#         window=12,
#         poly_order=4,
#         auto_update_final_col=False,
#     )
#     smoothed_data = smoother.apply_smoothing()
#     smoothed_col = smoother.create_new_column_name()
#     assert len(smoothed_data) == len(data_to_smooth_hourly)
#     assert smoothed_col == "epithermal_neutrons_savgol_12_4"
#     og_data_table[smoothed_col] = smoothed_data
#     assert smoothed_col in og_data_table.columns


@pytest.mark.reset_columns
def test_update_col_name_final(data_to_smooth_hourly):
    """
    Test to check ColumnInfo is auto updated when turned on.
    """
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
            smooth_method="savitsky_golay",
            window=12,
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
