import pandas as pd
from neptoon.data_management.crns_data_hub import CRNSDataHub
from neptoon.quality_assesment.quality_assesment import (
    FlagSpikeDetectionUniLOF,
    QualityAssessmentFlagBuilder,
    FlagRangeCheck,
)


def test_apply_custom_flags_CRNSDataHub():
    df = pd.DataFrame(
        {"A": [1, 2, 11]}, index=pd.date_range("2023-01-01", periods=3)
    )
    data_hub = CRNSDataHub(crns_data_frame=df)
    qa_flags = QualityAssessmentFlagBuilder()
    qa_flags.add_check(
        FlagRangeCheck("A", min_val=0, max_val=10),
        FlagSpikeDetectionUniLOF("A"),
    )
    data_hub.apply_quality_flags(custom_flags=qa_flags)
