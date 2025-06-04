# tests/test_pressure_unit_conversion.py
import pandas as pd
import pytest

from neptoon.io.read.data_ingest import (
    InputDataFrameFormattingConfig,
    FormatDataForCRNSDataHub,
    InputColumnMetaData,
    InputColumnDataType,
    PressureUnits,
)


@pytest.fixture
def base_config():
    cfg = InputDataFrameFormattingConfig(path_to_config=None)
    return cfg


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
