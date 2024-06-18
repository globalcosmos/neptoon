# %%
import pandas
import datetime
from pathlib import Path
import pandas.api.types as ptypes

from neptoon.data_ingest_and_formatting.data_ingest import (
    ManageFileCollection,
    ParseFilesIntoDataFrame,
    FormatDataForCRNSDataHub,
)

test_dir_path = Path(__file__).parent / "mock_data" / "test_dir"

test_filename = (
    Path(__file__).parent / "mock_data" / "CRNS-station_data-Hydroinnova-A.zip"
)


# %%
def test_collect_files_from_folder(
    path=test_dir_path,
):
    """
    Test the collection of files from a folder
    """
    file_manager = ManageFileCollection(path)
    file_manager.get_list_of_files()
    files = file_manager.files
    assert isinstance(files, list)
    assert len(files) == 4


test_collect_files_from_folder()


# %%
def test_collect_files_from_archive(
    filename=test_filename,
):
    """
    Test the collection of files from an archive
    """
    file_manager = ManageFileCollection(filename)
    file_manager.get_list_of_files()
    files = file_manager.files
    assert isinstance(files, list)
    assert len(files) == 1082


test_collect_files_from_archive()


# %%
def test_filter_files(
    filename=test_filename,
    prefix="CRS03_Data18",
):
    """
    Test the filtering of file names in a file list
    """
    file_manager = ManageFileCollection(filename, prefix=prefix)
    file_manager.get_list_of_files()
    file_manager.filter_files()
    files_filtered = file_manager.files

    assert isinstance(files_filtered, list)
    assert len(files_filtered) == 47


test_filter_files()


# %%
def test_merge_files_from_archive(
    filename=test_filename,
    prefix="CRS03_Data",
):
    file_manager = ManageFileCollection(filename, prefix=prefix)
    file_manager.get_list_of_files()
    file_manager.filter_files()

    file_parser = ParseFilesIntoDataFrame(file_manager)
    data_str = file_parser._merge_files()

    assert isinstance(data_str, str)
    assert len(data_str) == 4884968


test_merge_files_from_archive()


# %%
def test_merge_files_from_folder(folder=test_dir_path, prefix="CRS03_Data"):
    file_manager = ManageFileCollection(folder, prefix=prefix)
    file_manager.get_list_of_files()
    file_manager.filter_files()

    file_parser = ParseFilesIntoDataFrame(file_manager)
    data_str = file_parser._merge_files()

    assert isinstance(data_str, str)
    assert len(data_str) == 17952


test_merge_files_from_folder()


# %%
def test_guess_header(folder=test_dir_path, prefix="CRS03_Data"):
    file_manager = ManageFileCollection(folder, prefix=prefix)
    file_manager.get_list_of_files()
    file_manager.filter_files()

    file_parser = ParseFilesIntoDataFrame(file_manager)
    column_names = file_parser._infer_column_names()

    assert column_names == [
        "RecordNum",
        "Date Time(UTC)",
        "P1_mb",
        "P3_mb",
        "P4_mb",
        "T1_C",
        "T2_C",
        "T3_C",
        "T4_C",
        "T_CS215",
        "RH1",
        "RH2",
        "RH_CS215",
        "Vbat",
        "N1Cts",
        "N2Cts",
        "N1ET_sec",
        "N2ET_sec",
        "N1T_C",
        "N1RH",
        "N2T_C",
        "N2RH",
        "D1",
        "",
    ]


test_guess_header()


# %%
def test_make_dateframe(
    folder=test_dir_path,
    prefix="CRS03_Data",
):
    file_manager = ManageFileCollection(folder, prefix=prefix)
    file_manager.get_list_of_files()
    file_manager.filter_files()

    file_parser = ParseFilesIntoDataFrame(file_manager)
    data = file_parser.make_dataframe()

    assert isinstance(data, pandas.DataFrame)
    assert data.shape == (96, 24)


test_make_dateframe()


# %%
def test_make_dataframe(
    folder=test_dir_path,
    prefix="CRS03_Data",
):
    file_manager = ManageFileCollection(folder, prefix=prefix)
    file_manager.get_list_of_files()
    file_manager.filter_files()

    file_parser = ParseFilesIntoDataFrame(file_manager)
    data = file_parser.make_dataframe()

    assert isinstance(data, pandas.DataFrame)
    assert data.shape == (96, 24)


test_make_dataframe()


# %%
def test_format_dataframe(
    folder=test_dir_path,
    prefix="CRS03_Data",
):
    file_manager = ManageFileCollection(folder, prefix=prefix)
    file_manager.get_list_of_files()
    file_manager.filter_files()

    file_parser = ParseFilesIntoDataFrame(file_manager)
    data = file_parser.make_dataframe()

    data_formatter = FormatDataForCRNSDataHub(data, 1)

    datetime_series = data_formatter.extract_datetime_column()
    assert ptypes.is_datetime64_any_dtype(datetime_series)

    datetime_series_tz = data_formatter.convert_time_zone(datetime_series)
    assert datetime_series_tz.dt.tz == datetime.timezone.utc

    data_formatter.datetime_as_index()
    assert isinstance(
        data_formatter.data_frame.index,
        pandas.core.indexes.datetimes.DatetimeIndex,
    )

    data_formatter.dataframe_to_numeric()
    data = data_formatter.data_frame
    assert data["P1_mb"].dtype.kind == "f"
    data.P1_mb.plot(ls="", marker="o")


test_format_dataframe()


# %%
