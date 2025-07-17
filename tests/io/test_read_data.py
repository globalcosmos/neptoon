# tests/test_pressure_unit_conversion.py
import pandas as pd
import pytest
import datetime

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
