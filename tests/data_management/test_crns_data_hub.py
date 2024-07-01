# import pandas as pd
# from neptoon.data_management.crns_data_hub import CRNSDataHub
# import pytest
# from neptoon.quality_assesment.quality_assesment import (
#     FlagSpikeDetectionUniLOF,
#     QualityAssessmentFlagBuilder,
#     FlagRangeCheck,
# )
# from unittest.mock import Mock, patch


# @pytest.fixture
# def sample_crns_data():
#     return pd.DataFrame(
#         {
#             "date_time": pd.date_range(
#                 start="2023-01-01", periods=5, freq="H"
#             ),
#             "epithermal_neutrons": [100, 110, 105, 115, 108],
#             "air_pressure": [1000, 1005, 1002, 998, 1001],
#             "air_relative_humidity": [80, 75, 76, 65, 89],
#             "air_temperature": [23, 24, 25, 23, 20],
#         }
#     ).set_index("datetime")


# @pytest.fixture
# def example_data_hub(sample_crns_data):
#     return CRNSDataHub(crns_data_frame=sample_crns_data)


# def test_crns_data_hub_initialization(sample_crns_data):
#     """
#     Assert that the data_hub is initialised correctly
#     """
#     data_hub = CRNSDataHub(crns_data_frame=sample_crns_data)
#     assert isinstance(data_hub, CRNSDataHub)
#     assert data_hub.crns_data_frame.equals(sample_crns_data)


# @patch(
#     "neptoon.ancillary_data_collection.nmdb_data_collection.NMDBDataAttacher"
# )
# def test_attach_nmdb_data(mock_nmdb_attacher, crns_data_hub):
#     crns_data_hub.attach_nmdb_data()
#     mock_nmdb_attacher.assert_called_once()
#     mock_nmdb_attacher.return_value.configure.assert_called_once()
#     mock_nmdb_attacher.return_value.fetch_data.assert_called_once()
#     mock_nmdb_attacher.return_value.attach_data.assert_called_once()


# def test_apply_quality_flags(crns_data_hub):
#     mock_flag_builder = Mock(spec=QualityAssessmentFlagBuilder)
#     crns_data_hub.apply_quality_flags(custom_flags=mock_flag_builder)
#     assert crns_data_hub.quality_assessor is not None
#     assert isinstance(crns_data_hub.flags_data_frame, pd.DataFrame)


# def test_apply_custom_flags_CRNSDataHub():
#     df = pd.DataFrame(
#         {"A": [1, 2, 11]}, index=pd.date_range("2023-01-01", periods=3)
#     )
#     data_hub = CRNSDataHub(crns_data_frame=sample_crns_data)
#     qa_flags = QualityAssessmentFlagBuilder()
#     qa_flags.add_check(
#         FlagRangeCheck("air_temperature", min_val=22, max_val=29),
#         FlagSpikeDetectionUniLOF("epithermal_neutrons"),
#     )
#     data_hub.apply_quality_flags(custom_flags=qa_flags)
