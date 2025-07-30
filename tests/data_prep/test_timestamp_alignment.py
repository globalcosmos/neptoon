import pandas as pd
from pathlib import Path
import pytest
from neptoon.data_prep.timestamp_alignment import (
    TimeStampAligner,
    TimeStampAggregator,
)
from neptoon.utils import recalculate_neutron_uncertainty
from neptoon.columns import ColumnInfo


@pytest.fixture
def correct_df():
    data_path = Path(__file__).parent.parent / "test_data" / "io"
    return pd.read_csv(
        data_path / "unprocessed_df.csv",
        index_col=0,
        parse_dates=True,
    )


def test_create_aligner_object_correct_format(correct_df):
    """
    Test the creation of the object. Test checks for when data is
    formatted correctly.
    """

    ts_align = TimeStampAligner(correct_df)
    assert isinstance(ts_align, TimeStampAligner)


def test_create_aligner_object_wrong_format(correct_df):
    """
    Test the creation of the object. Test checks for when data is not
    formatted correctly (i.e., not datetime index).
    """
    bad_df = correct_df
    bad_df.index = bad_df.index.astype(str)
    with pytest.raises(
        ValueError, match="The DataFrame index must be of datetime type"
    ):
        TimeStampAligner(bad_df)


# def test_align_timestamps():
#     """_summary_"""
#     data_path = Path(__file__).parent / "mock_data"
#     data_before_alignment = pd.read_csv(
#         data_path / "unprocessed_df.csv",
#         index_col=0,
#         parse_dates=True,
#     )
#     data_aligned = pd.read_csv(
#         data_path / "processed_df.csv",
#         index_col=0,
#         parse_dates=True,
#     )
#     tsa = TimeStampAligner(data_before_alignment)
#     tsa.align_timestamps()
#     result_df = tsa.return_dataframe()

#     pd.testing.assert_frame_equal(result_df, data_aligned, check_freq=False)


def test_return_dataframe(correct_df):
    ts_align = TimeStampAligner(correct_df)
    df = ts_align.return_dataframe()
    assert isinstance(df, pd.DataFrame)


#############################
#   TimeStamp Aggregation   #
#############################


@pytest.fixture
def time_stamp_aggregator(correct_df):
    ts_agg = TimeStampAggregator(
        data_frame=correct_df,
        output_resolution="1hour",
        max_na_fraction=0.3,
    )
    return ts_agg


## Correct df has 15 min resolution
def test_timedelta_to_freq_str(time_stamp_aggregator):
    ts_agg = time_stamp_aggregator
    assert ts_agg.avg_temporal_scaling_factor == 4
    assert ts_agg.max_na_int == 1


def test_rescale_uncertainty(correct_df):
    data_frame = correct_df
    data_frame[
        str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UNCERTAINTY)
    ] = 20
    recalculate_neutron_uncertainty(
        data_frame=data_frame,
        temporal_scaling_factor=4,
    )
    assert (
        data_frame[
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_UNCERTAINTY)
        ].iloc[0]
        == 10
    )
