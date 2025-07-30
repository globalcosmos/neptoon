# tests/test_pressure_unit_conversion.py
import pandas as pd
import pytest
import datetime
import numpy as np
from neptoon.io.read.data_ingest import (
    InputDataFrameFormattingConfig,
    FormatDataForCRNSDataHub,
    InputColumnMetaData,
    InputColumnDataType,
    PressureUnits,
)
from neptoon.columns import ColumnInfo


@pytest.fixture
def base_config():
    cfg = InputDataFrameFormattingConfig(path_to_config=None)
    return cfg


@pytest.fixture
def base_df():
    df = pd.DataFrame(
        {
            str(ColumnInfo.Name.DATE_TIME): pd.date_range(
                "2022-01-01", periods=5
            ),
        }
    )
    return df


@pytest.fixture
def df_formatter(base_df, base_config):
    df = base_df
    return FormatDataForCRNSDataHub(data_frame=df, config=base_config)


def test_extract_date_time_column(df_formatter):
    series = df_formatter.extract_date_time_column()
    assert isinstance(series, pd.Series)
    assert isinstance(series[0], datetime.datetime)


def test_extract_date_time_column(df_formatter):
    series = df_formatter.extract_date_time_column()
    assert isinstance(series, pd.Series)
    assert isinstance(series[0], datetime.datetime)


def test_extract_date_time_column_list(df_formatter, base_df):
    df_formatter.config.date_time_columns = ["date", "time"]
    df = base_df
    df["date"] = base_df[str(ColumnInfo.Name.DATE_TIME)].dt.date
    df["time"] = base_df[str(ColumnInfo.Name.DATE_TIME)].dt.time
    series = df_formatter.extract_date_time_column()
    assert isinstance(series, pd.Series)
    assert isinstance(series[0], datetime.datetime)


def test_pascals_to_hectopascals(base_config):
    df = pd.DataFrame({"P_raw": [101325, 100000, 98000]})

    base_config.column_data = [
        InputColumnMetaData(
            initial_name="P_raw",
            variable_type=InputColumnDataType.PRESSURE,
            unit=PressureUnits.PASCALS,
            priority=1,
        )
    ]
    formatter = FormatDataForCRNSDataHub(
        data_frame=df.copy(), config=base_config
    )
    formatter.standardise_units_of_pressure()
    out = formatter.data_frame

    expected = df["P_raw"] / 100
    pd.testing.assert_series_equal(out["P_raw"], expected, check_names=False)

    assert base_config.column_data[0].unit == PressureUnits.HECTOPASCALS


def test_kilopascals_to_hectopascals(base_config):
    df = pd.DataFrame({"P_kpa": [101.325, 100.0, 98.0]})

    base_config.column_data = [
        InputColumnMetaData(
            initial_name="P_kpa",
            variable_type=InputColumnDataType.PRESSURE,
            unit=PressureUnits.KILOPASCALS,
            priority=1,
        )
    ]

    formatter = FormatDataForCRNSDataHub(
        data_frame=df.copy(), config=base_config
    )
    formatter.standardise_units_of_pressure()
    out = formatter.data_frame

    expected = df["P_kpa"] * 10
    pd.testing.assert_series_equal(out["P_kpa"], expected, check_names=False)

    assert base_config.column_data[0].unit == PressureUnits.HECTOPASCALS


###############
@pytest.fixture
def base_config():
    cfg = InputDataFrameFormattingConfig(path_to_config=None)
    return cfg


@pytest.fixture
def base_df():
    df = pd.DataFrame(
        {
            str(ColumnInfo.Name.DATE_TIME): pd.date_range(
                "2022-01-01", periods=5, freq="1h"
            ),
        }
    )
    return df


@pytest.fixture
def df_formatter(base_df, base_config):
    df = base_df
    return FormatDataForCRNSDataHub(data_frame=df, config=base_config)


def test_conversion_factor_to_cph_one_hour(df_formatter):
    """Test conversion factor calculation for 1-hour timestep."""
    factor = df_formatter.get_conversion_factor_to_cph(3600)
    assert factor == 1.0


def test_conversion_factor_to_cph_thirty_minutes(df_formatter):
    """Test conversion factor calculation for 30-minute timestep."""
    factor = df_formatter.get_conversion_factor_to_cph(1800)
    assert factor == 2.0


def test_conversion_factor_to_cph_one_minute(df_formatter):
    """Test conversion factor calculation for 1-minute timestep."""
    factor = df_formatter.get_conversion_factor_to_cph(60)
    assert factor == 60.0


def test_epi_neutron_counts_per_hour_conversion(base_config):
    """Test conversion when epi neutron data is already in counts_per_hour."""

    epi_col = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)
    df = pd.DataFrame(
        {
            epi_col: [
                100,
                200,
                150,
                300,
                250,
            ],
            str(ColumnInfo.Name.DATE_TIME): pd.date_range(
                "2022-01-01", periods=5, freq="1h"
            ),
        }
    )

    base_config.column_data = [
        InputColumnMetaData(
            initial_name=epi_col,
            variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit="counts_per_hour",
            priority=1,
        )
    ]
    base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

    formatter = FormatDataForCRNSDataHub(
        data_frame=df.copy(), config=base_config
    )
    formatter.date_time_as_index()
    formatter.prepare_neutron_count_columns(
        neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
    )

    out = formatter.data_frame

    # Original CPH values should be preserved in the final column
    expected_cph = [100, 200, 150, 300, 250]
    actual_cph = out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)].tolist()
    assert actual_cph == expected_cph


def test_epi_neutron_absolute_count_conversion(base_config):
    """Test conversion from absolute_count to counts_per_hour."""
    epi_col = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)

    df = pd.DataFrame(
        {
            epi_col: [100, 200, 150, 300, 250],
            str(ColumnInfo.Name.DATE_TIME): pd.date_range(
                "2022-01-01", periods=5, freq="1h"
            ),
        }
    )

    base_config.column_data = [
        InputColumnMetaData(
            initial_name="epi_raw",
            variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit="absolute_count",
            priority=1,
        )
    ]
    base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

    formatter = FormatDataForCRNSDataHub(
        data_frame=df.copy(), config=base_config
    )
    formatter.date_time_as_index()
    formatter.prepare_neutron_count_columns(
        neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
    )

    out = formatter.data_frame

    # For 1-hour timesteps, absolute counts should equal CPH
    # first val will be nan as no diff possible here
    expected_cph = [np.nan, 200, 150, 300, 250]
    out_list = out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)].to_list()

    np.testing.assert_array_equal(out_list, expected_cph)


def test_epi_neutron_absolute_count_thirty_minute_timestep(base_config):
    """Test conversion from absolute_count to counts_per_hour with 30-minute timestep."""
    epi_col = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)
    df = pd.DataFrame(
        {
            epi_col: [50, 100, 75, 150, 125],  # Half-hour absolute counts
            str(ColumnInfo.Name.DATE_TIME): pd.date_range(
                "2022-01-01", periods=5, freq="30min"
            ),
        }
    )

    base_config.column_data = [
        InputColumnMetaData(
            initial_name="epi_raw",
            variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit="absolute_count",
            priority=1,
        )
    ]
    base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

    formatter = FormatDataForCRNSDataHub(
        data_frame=df.copy(), config=base_config
    )
    formatter.date_time_as_index()
    formatter.prepare_neutron_count_columns(
        neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
    )

    out = formatter.data_frame

    # For 30-minute timesteps, CPH should be double the absolute count
    expected_cph = [np.nan, 200, 150, 300, 250]
    out_list = out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)].to_list()

    np.testing.assert_array_equal(out_list, expected_cph)


def test_epi_neutron_counts_per_second_conversion(base_config):
    """Test conversion from counts_per_second to counts_per_hour."""
    epi_col = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)
    df = pd.DataFrame(
        {
            epi_col: [1.0, 2.0, 0.5, 3.0, 1.5],  # counts per second
            str(ColumnInfo.Name.DATE_TIME): pd.date_range(
                "2022-01-01", periods=5, freq="1h"
            ),
        }
    )

    base_config.column_data = [
        InputColumnMetaData(
            initial_name=epi_col,
            variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit="counts_per_second",
            priority=1,
        )
    ]
    base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

    formatter = FormatDataForCRNSDataHub(
        data_frame=df.copy(), config=base_config
    )
    formatter.date_time_as_index()
    formatter.prepare_neutron_count_columns(
        neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
    )

    out = formatter.data_frame

    # CPH should be counts_per_second * 3600
    expected_cph = [3600, 7200, 1800, 10800, 5400]
    out_cph = out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)].to_list()
    np.testing.assert_array_equal(out_cph, expected_cph)

    # Raw values should be converted to absolute counts (cps * timestep_seconds)
    expected_raw = [np.nan, 7200, 1800, 10800, 5400]
    out_raw = out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)].to_list()
    np.testing.assert_array_equal(out_raw, expected_raw)


## REFORMAT FROM HERE


# def test_neutron_uncertainty_calculation(base_config):
#     """Test neutron count uncertainty calculation."""
#     df = pd.DataFrame(
#         {
#             "epi_raw": [
#                 100,
#                 400,
#                 900,
#                 1600,
#             ],  # Perfect squares for easy testing
#             str(ColumnInfo.Name.DATE_TIME): pd.date_range(
#                 "2022-01-01", periods=4, freq="1H"
#             ),
#         }
#     )

#     base_config.column_data = [
#         InputColumnMetaData(
#             initial_name="epi_raw",
#             variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
#             unit="absolute_count",
#             priority=1,
#         )
#     ]
#     base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

#     formatter = FormatDataForCRNSDataHub(
#         data_frame=df.copy(), config=base_config
#     )
#     formatter.date_time_as_index()
#     formatter.prepare_neutron_count_columns(
#         neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
#     )
#     formatter.calc_neutron_uncertainty()

#     out = formatter.data_frame

#     # Uncertainty should be sqrt of raw counts (for 1-hour timestep, conversion factor = 1)
#     expected_uncertainty = pd.Series(
#         [10, 20, 30, 40],
#         name=str(ColumnInfo.Name.RAW_EPI_NEUTRON_COUNT_UNCERTAINTY),
#     )
#     pd.testing.assert_series_equal(
#         out[str(ColumnInfo.Name.RAW_EPI_NEUTRON_COUNT_UNCERTAINTY)],
#         expected_uncertainty,
#         check_names=False,
#     )


# def test_neutron_uncertainty_with_thirty_minute_timestep(base_config):
#     """Test neutron count uncertainty calculation with 30-minute timestep."""
#     df = pd.DataFrame(
#         {
#             "epi_raw": [100, 400, 900],  # Perfect squares
#             str(ColumnInfo.Name.DATE_TIME): pd.date_range(
#                 "2022-01-01", periods=3, freq="30T"
#             ),
#         }
#     )

#     base_config.column_data = [
#         InputColumnMetaData(
#             initial_name="epi_raw",
#             variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
#             unit="absolute_count",
#             priority=1,
#         )
#     ]
#     base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

#     formatter = FormatDataForCRNSDataHub(
#         data_frame=df.copy(), config=base_config
#     )
#     formatter.date_time_as_index()
#     formatter.prepare_neutron_count_columns(
#         neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
#     )
#     formatter.calc_neutron_uncertainty()

#     out = formatter.data_frame

#     # Uncertainty should be sqrt(raw_counts) * conversion_factor_to_cph
#     # For 30-minute timestep: conversion_factor = 2.0
#     expected_uncertainty = pd.Series(
#         [20, 40, 60],
#         name=str(ColumnInfo.Name.RAW_EPI_NEUTRON_COUNT_UNCERTAINTY),
#     )
#     pd.testing.assert_series_equal(
#         out[str(ColumnInfo.Name.RAW_EPI_NEUTRON_COUNT_UNCERTAINTY)],
#         expected_uncertainty,
#         check_names=False,
#     )


# def test_multiple_epi_neutron_columns_merge(base_config):
#     """Test merging multiple epithermal neutron columns."""
#     df = pd.DataFrame(
#         {
#             "epi_1": [50, 100, 75, 150, 125],
#             "epi_2": [30, 80, 45, 120, 95],
#             "epi_3": [20, 60, 30, 90, 70],
#             str(ColumnInfo.Name.DATE_TIME): pd.date_range(
#                 "2022-01-01", periods=5, freq="1H"
#             ),
#         }
#     )

#     base_config.column_data = [
#         InputColumnMetaData(
#             initial_name="epi_1",
#             variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
#             unit="absolute_count",
#             priority=1,
#         ),
#         InputColumnMetaData(
#             initial_name="epi_2",
#             variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
#             unit="absolute_count",
#             priority=2,
#         ),
#         InputColumnMetaData(
#             initial_name="epi_3",
#             variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
#             unit="absolute_count",
#             priority=3,
#         ),
#     ]
#     base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

#     formatter = FormatDataForCRNSDataHub(
#         data_frame=df.copy(), config=base_config
#     )
#     formatter.date_time_as_index()
#     formatter.prepare_neutron_count_columns(
#         neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
#     )

#     out = formatter.data_frame

#     # Raw column should be the sum of all epi columns
#     expected_raw = pd.Series(
#         [100, 240, 150, 360, 290],
#         name=str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW),
#     )
#     pd.testing.assert_series_equal(
#         out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)],
#         expected_raw,
#         check_names=False,
#     )

#     # CPH should equal raw for 1-hour timestep with absolute_count unit
#     pd.testing.assert_series_equal(
#         out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)],
#         expected_raw,
#         check_names=False,
#     )


# def test_round_trip_conversion_counts_per_hour_to_absolute_and_back(
#     base_config,
# ):
#     """Test that counts_per_hour conversion is reversible."""
#     original_cph = [100, 200, 300]
#     df = pd.DataFrame(
#         {
#             "epi_raw": original_cph,
#             str(ColumnInfo.Name.DATE_TIME): pd.date_range(
#                 "2022-01-01", periods=3, freq="1H"
#             ),
#         }
#     )

#     base_config.column_data = [
#         InputColumnMetaData(
#             initial_name="epi_raw",
#             variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
#             unit="counts_per_hour",
#             priority=1,
#         )
#     ]
#     base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

#     formatter = FormatDataForCRNSDataHub(
#         data_frame=df.copy(), config=base_config
#     )
#     formatter.date_time_as_index()
#     formatter.prepare_neutron_count_columns(
#         neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
#     )

#     out = formatter.data_frame

#     # Should recover original CPH values
#     recovered_cph = out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)]
#     expected_cph = pd.Series(
#         original_cph, name=str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)
#     )
#     pd.testing.assert_series_equal(
#         recovered_cph, expected_cph, check_names=False
#     )


def test_neutron_uncertainty_calculation(base_config):
    """Test neutron count uncertainty calculation."""
    epi_col = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)
    df = pd.DataFrame(
        {
            epi_col: [
                100,
                400,
                900,
                1600,
            ],  # Perfect squares for easy testing
            str(ColumnInfo.Name.DATE_TIME): pd.date_range(
                "2022-01-01", periods=4, freq="1h"
            ),
        }
    )

    base_config.column_data = [
        InputColumnMetaData(
            initial_name=epi_col,
            variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit="absolute_count",
            priority=1,
        )
    ]
    base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

    formatter = FormatDataForCRNSDataHub(
        data_frame=df.copy(), config=base_config
    )
    formatter.date_time_as_index()
    formatter.prepare_neutron_count_columns(
        neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
    )
    formatter.calc_neutron_uncertainty()

    out = formatter.data_frame

    # Uncertainty should be sqrt of raw counts (for 1-hour timestep, conversion factor = 1)
    expected_uncertainty = [np.nan, 20, 30, 40]
    out_uncertainty = out[
        str(ColumnInfo.Name.RAW_EPI_NEUTRON_COUNT_UNCERTAINTY)
    ].to_list()
    np.testing.assert_array_equal(out_uncertainty, expected_uncertainty)


def test_neutron_uncertainty_with_thirty_minute_timestep(base_config):
    """Test neutron count uncertainty calculation with 30-minute timestep."""
    epi_col = str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)
    df = pd.DataFrame(
        {
            epi_col: [100, 400, 900],  # Perfect squares
            str(ColumnInfo.Name.DATE_TIME): pd.date_range(
                "2022-01-01", periods=3, freq="30min"
            ),
        }
    )

    base_config.column_data = [
        InputColumnMetaData(
            initial_name=epi_col,
            variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit="absolute_count",
            priority=1,
        )
    ]
    base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

    formatter = FormatDataForCRNSDataHub(
        data_frame=df.copy(), config=base_config
    )
    formatter.date_time_as_index()
    formatter.prepare_neutron_count_columns(
        neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
    )
    formatter.calc_neutron_uncertainty()

    out = formatter.data_frame

    # Uncertainty should be sqrt(raw_counts) * conversion_factor_to_cph
    # For 30-minute timestep: conversion_factor = 2.0
    expected_uncertainty = [np.nan, 40, 60]
    out_uncertainty = out[
        str(ColumnInfo.Name.RAW_EPI_NEUTRON_COUNT_UNCERTAINTY)
    ].to_list()
    np.testing.assert_array_equal(out_uncertainty, expected_uncertainty)


def test_multiple_epi_neutron_columns_merge(base_config):
    """Test merging multiple epithermal neutron columns."""
    df = pd.DataFrame(
        {
            "epi_1": [50, 100, 75, 150, 125],
            "epi_2": [30, 80, 45, 120, 95],
            "epi_3": [20, 60, 30, 90, 70],
            str(ColumnInfo.Name.DATE_TIME): pd.date_range(
                "2022-01-01", periods=5, freq="1h"
            ),
        }
    )

    base_config.column_data = [
        InputColumnMetaData(
            initial_name="epi_1",
            variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit="absolute_count",
            priority=1,
        ),
        InputColumnMetaData(
            initial_name="epi_2",
            variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit="absolute_count",
            priority=2,
        ),
        InputColumnMetaData(
            initial_name="epi_3",
            variable_type=InputColumnDataType.EPI_NEUTRON_COUNT,
            unit="absolute_count",
            priority=3,
        ),
    ]
    base_config.date_time_columns = str(ColumnInfo.Name.DATE_TIME)

    formatter = FormatDataForCRNSDataHub(
        data_frame=df.copy(), config=base_config
    )
    formatter.date_time_as_index()
    formatter.prepare_neutron_count_columns(
        neutron_column_type=InputColumnDataType.EPI_NEUTRON_COUNT
    )

    out = formatter.data_frame

    # Raw column should be the sum of all epi columns
    expected_raw = [100, 240, 150, 360, 290]
    out_raw = out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW)].to_list()
    np.testing.assert_array_equal(out_raw, expected_raw)

    # CPH should equal raw for 1-hour timestep with absolute_count unit (first value NaN due to diff)
    expected_cph = [np.nan, 240, 150, 360, 290]
    out_cph = out[str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH)].to_list()
    np.testing.assert_array_equal(out_cph, expected_cph)
