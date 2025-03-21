# %%
import pandas as pd
from pathlib import Path

# import pandas.api.types as ptypes

# %%
from neptoon.io.read.data_ingest import (
    # ManageFileCollection,
    # ParseFilesIntoDataFrame,
    # FormatDataForCRNSDataHub,
    CollectAndParseRawData,
)

test_dir_path = Path(__file__).parent.parent / "test_data" / "io" / "test_dir"

test_filename = (
    Path(__file__).parent
    / "test_data"  # COME BACK TO THIS <-- remove i think #####!!!##
    / "io"
    / "CRNS-station_data-Hydroinnova-A.zip"
)

config_path = (
    Path(__file__).parent.parent
    / "test_data"
    / "io"
    / "A101_station_test.yaml"
)

"""
Full tests to be written. For now we include a canary that checks the
whole YAML run. If this breaks we investigate where it broke.
"""


# %%
def test_canary(
    config_path=config_path,
):
    data_creator = CollectAndParseRawData(path_to_config=config_path)
    df = data_creator.create_data_frame()
    assert "air_pressure" in df.columns
    assert "epithermal_neutrons_cph" in df.columns
    assert isinstance(
        df.index, pd.DatetimeIndex
    ), "DataFrame index is not a DatetimeIndex"
    assert df.index.tz is not None, "DataFrame index is not timezone-aware"
    assert not df.empty, "DataFrame is empty"
    assert (
        df["air_pressure"].dtype == "float64"
    ), "air_pressure column is not float64"
    assert (
        df["epithermal_neutrons_cph"].dtype == "float64"
    ), "epithermal_neutrons_cph column is not float64"


# test_canary()

# # %%
# def test_collect_files_from_folder(
#     path=test_dir_path,
# ):
#     """
#     Test the collection of files from a folder
#     """
#     file_manager = ManageFileCollection(path)
#     file_manager.get_list_of_files()
#     files = file_manager.files
#     assert isinstance(files, list)
#     assert len(files) == 4


# # %%
# def test_collect_files_from_archive(
#     filename=test_filename,
# ):
#     """
#     Test the collection of files from an archive
#     """
#     file_manager = ManageFileCollection(filename)
#     file_manager.get_list_of_files()
#     files = file_manager.files
#     assert isinstance(files, list)
#     assert len(files) == 1082


# test_collect_files_from_archive()


# # %%
# def test_filter_files(
#     filename=test_filename,
#     prefix="CRS03_Data18",
# ):
#     """
#     Test the filtering of file names in a file list
#     """
#     file_manager = ManageFileCollection(filename, prefix=prefix)
#     file_manager.get_list_of_files()
#     file_manager.filter_files()
#     files_filtered = file_manager.files

#     assert isinstance(files_filtered, list)
#     assert len(files_filtered) == 47


# test_filter_files()


# # %%
# def test_merge_files_from_archive(
#     filename=test_filename,
#     prefix="CRS03_Data",
# ):
#     file_manager = ManageFileCollection(filename, prefix=prefix)
#     file_manager.get_list_of_files()
#     file_manager.filter_files()

#     file_parser = ParseFilesIntoDataFrame(file_manager)
#     data_str = file_parser._merge_files()

#     assert isinstance(data_str, str)
#     assert len(data_str) == 4884968


# test_merge_files_from_archive()


# # %%
# def test_merge_files_from_folder(folder=test_dir_path, prefix="CRS03_Data"):
#     file_manager = ManageFileCollection(folder, prefix=prefix)
#     file_manager.get_list_of_files()
#     file_manager.filter_files()

#     file_parser = ParseFilesIntoDataFrame(file_manager)
#     data_str = file_parser._merge_files()

#     assert isinstance(data_str, str)
#     assert len(data_str) == 17952


# test_merge_files_from_folder()


# # %%
# def test_guess_header(folder=test_dir_path, prefix="CRS03_Data"):
#     file_manager = ManageFileCollection(folder, prefix=prefix)
#     file_manager.get_list_of_files()
#     file_manager.filter_files()

#     file_parser = ParseFilesIntoDataFrame(file_manager)
#     column_names = file_parser._infer_column_names()

#     assert column_names == [
#         "RecordNum",
#         "Date Time(UTC)",
#         "P1_mb",
#         "P3_mb",
#         "P4_mb",
#         "T1_C",
#         "T2_C",
#         "T3_C",
#         "T4_C",
#         "T_CS215",
#         "RH1",
#         "RH2",
#         "RH_CS215",
#         "Vbat",
#         "N1Cts",
#         "N2Cts",
#         "N1ET_sec",
#         "N2ET_sec",
#         "N1T_C",
#         "N1RH",
#         "N2T_C",
#         "N2RH",
#         "D1",
#         "",
#     ]


# test_guess_header()


# # %%
# def test_make_dateframe(
#     folder=test_dir_path,
#     prefix="CRS03_Data",
# ):
#     file_manager = ManageFileCollection(folder, prefix=prefix)
#     file_manager.get_list_of_files()
#     file_manager.filter_files()

#     file_parser = ParseFilesIntoDataFrame(file_manager)
#     data = file_parser.make_dataframe()

#     assert isinstance(data, pandas.DataFrame)
#     assert data.shape == (96, 24)


# test_make_dateframe()


# # %%
# def test_make_dataframe(
#     folder=test_dir_path,
#     prefix="CRS03_Data",
# ):
#     file_manager = ManageFileCollection(folder, prefix=prefix)
#     file_manager.get_list_of_files()
#     file_manager.filter_files()

#     file_parser = ParseFilesIntoDataFrame(file_manager)
#     data = file_parser.make_dataframe()

#     assert isinstance(data, pandas.DataFrame)
#     assert data.shape == (96, 24)


# test_make_dataframe()
