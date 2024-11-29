import pytest
from unittest.mock import MagicMock
import pandas as pd
from saqc import SaQC
from neptoon.quality_control.quality_assesment_old import (
    DateTimeIndexValidator,
    QualityCheck,
    FlagRangeCheck,
    FlagSpikeDetectionUniLOF,
    QualityAssessmentFlagBuilder,
    DataQualityAssessor,
)
from neptoon.quality_control.quality_assesment import *


@pytest.fixture
def df():
    df = pd.DataFrame(
        {
            "range": [
                400,
                500,
                400,
                300,
                500,
            ],
            "spike": [
                1010,
                2000,
                2300,
                2300,
                8000,
            ],
        }
    )
    return df


def test_quality_check_validation():
    assert QualityCheck(
        target=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
        method=QAMethod.RANGE_CHECK,
        raw_params={"lower_bound": 500, "upper_bound": 550},
    )
    with pytest.raises(ValidationError):
        check = QualityCheck(
            target=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
            method=QAMethod.RANGE_CHECK,
            raw_params={"lower_bound": 500},
        )


def test_wrong_param_supplied(df):
    with pytest.raises(ValidationError):
        check = QualityCheck(
            target=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
            method=QAMethod.RANGE_CHECK,
            raw_params={
                "lower_bound": 500,
                "upper_bound": 550,
                "crazy_param": 550,
            },
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


def test_quality_check_cannot_be_instantiated():
    with pytest.raises(TypeError):
        QualityCheck()


def test_flag_range_check():
    qc = MagicMock(spec=SaQC)
    flag_range_check = FlagRangeCheck(column="A", min_val=0, max_val=10)
    flag_range_check.apply(qc)
    qc.flagRange.assert_called_with(field="A", min=0, max=10)


def test_flag_spike_detection_uni_lof():
    qc = MagicMock(spec=SaQC)
    flag_spike_detection = FlagSpikeDetectionUniLOF(
        column_name="A", periods_in_calculation=24, threshold=1.5
    )
    flag_spike_detection.apply(qc)
    qc.flagUniLOF.assert_called_with("A", n=24, thresh=1.5)


def test_quality_assessment_flag_builder():
    qc = MagicMock(spec=SaQC)
    builder = QualityAssessmentFlagBuilder()

    # Add a FlagRangeCheck
    flag_range_check = FlagRangeCheck(column="A", min_val=0, max_val=10)
    builder.add_check(flag_range_check)

    # Apply checks
    builder.apply_checks(qc)
    qc.flagRange.assert_called_with(field="A", min=0, max=10)


def test_quality_assessment_flag_builder_multiple():
    qc = MagicMock(spec=SaQC)
    builder = QualityAssessmentFlagBuilder()

    # Add a FlagRangeCheck
    flag_range_check = [
        FlagRangeCheck(column="A", min_val=0, max_val=10),
        FlagSpikeDetectionUniLOF("A"),
    ]
    builder.add_check(flag_range_check)

    # Apply checks
    builder.apply_checks(qc)
    # Should run with no errors


def test_data_quality_assessor_scheme_change():
    df = pd.DataFrame(
        {"A": [1, 2, 3]}, index=pd.date_range("2023-01-01", periods=3)
    )
    dqa = DataQualityAssessor(data_frame=df)

    # Test default SaQC scheme
    assert dqa.saqc_scheme == "simple"

    dqa.change_saqc_scheme("float")

    # Test changing scheme
    assert dqa.saqc_scheme == "float"

    # Test wrong scheme given
    with pytest.raises(TypeError):
        dqa.change_saqc_scheme("wrong_scheme")
