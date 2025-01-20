import pandas as pd
from pathlib import Path
import pytest
from neptoon.io.read.data_ingest import (
    TimeStampAligner,
)


def test_create_aligner_object_correct_format():
    """
    Test the creation of the object. Test checks for when data is
    formatted correctly.
    """
    data_path = Path(__file__).parent.parent / "test_data" / "io"
    data_correct_format = pd.read_csv(
        data_path / "unprocessed_df.csv",
        index_col=0,
        parse_dates=True,
    )
    tsa = TimeStampAligner(data_correct_format)
    assert isinstance(tsa, TimeStampAligner)


def test_create_aligner_object_wrong_format():
    """
    Test the creation of the object. Test checks for when data is not
    formatted correctly (i.e., not datetime index).
    """
    data_path = Path(__file__).parent.parent / "test_data" / "io"
    data_incorrect_format = pd.read_csv(
        data_path / "unprocessed_df.csv",
    )
    with pytest.raises(
        ValueError, match="The DataFrame index must be of datetime type"
    ):
        TimeStampAligner(data_incorrect_format)


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


# test_align_timestamps()


def test_return_dataframe():
    data_path = Path(__file__).parent.parent / "test_data" / "io"
    data_correct_format = pd.read_csv(
        data_path / "unprocessed_df.csv",
        index_col=0,
        parse_dates=True,
    )
    tsa = TimeStampAligner(data_correct_format)
    df = tsa.return_dataframe()
    assert isinstance(df, pd.DataFrame)
