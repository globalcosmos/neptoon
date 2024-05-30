# %%
import pandas
from pathlib import Path
import pytest
from neptoon.data_ingest_and_formatting.data_ingest import (
    collect_files_from_folder,
    collect_files_from_archive,
    filter_files,
    merge_files,
    guess_header,
    make_dataframe,
    make_datetime,
    datetime_as_index,
    dataframe_to_numeric
)

# %%
def test_collect_files_from_folder(
    path="mock_data/test_dir/"
):
    """
    Test the collection of files from a folder
    """
    files = collect_files_from_folder(path)
    assert isinstance(files, list)
    assert len(files) == 4

test_collect_files_from_folder()

# %%
def test_collect_files_from_archive(
    filename="mock_data/CRNS-station_data-Hydroinnova-A.zip"
):
    """
    Test the collection of files from an archive
    """
    files = collect_files_from_archive(filename)
    assert isinstance(files, list)
    assert len(files) == 1082

test_collect_files_from_archive()

# %%
def test_filter_files(
    filename="mock_data/CRNS-station_data-Hydroinnova-A.zip",
    prefix="CRS03_Data18"
):
    """
    Test the filtering of file names in a file list
    """
    files = collect_files_from_archive(filename)
    files_filtered = filter_files(files, prefix=prefix)
    assert isinstance(files_filtered, list)
    assert len(files_filtered) == 47

test_filter_files()

# %%
def test_merge_files_from_archive(
    filename="mock_data/CRNS-station_data-Hydroinnova-A.zip",
    prefix="CRS03_Data"
):
    files = collect_files_from_archive(filename)
    files_filtered = filter_files(files, prefix=prefix)
    
    data_str = merge_files(filename, files_filtered)
    # print(data_str)
    assert isinstance(data_str, str)
    assert len(data_str) == 4884968 

test_merge_files_from_archive()

# %%
def test_merge_files_from_folder(
    folder="mock_data/test_dir",
    prefix="CRS03_Data"
):
    files = collect_files_from_folder(folder)
    files_filtered = filter_files(files, prefix=prefix)
    
    data_str = merge_files(folder, files_filtered)
    assert isinstance(data_str, str)
    assert len(data_str) == 17952 

test_merge_files_from_folder()

# %%
def test_guess_header(
    folder="mock_data/test_dir",
    prefix="CRS03_Data"
):
    files = collect_files_from_folder(folder)
    files_filtered = filter_files(files, prefix=prefix, verbose=False)
    column_names = guess_header(folder, files_filtered[0])
    # print(column_names)
    assert column_names == ['RecordNum', 'Date Time(UTC)', 'P1_mb', 'P3_mb', 'P4_mb', 'T1_C', 'T2_C', 'T3_C', 'T4_C', 'T_CS215', 'RH1', 'RH2', 'RH_CS215', 'Vbat', 'N1Cts', 'N2Cts', 'N1ET_sec', 'N2ET_sec', 'N1T_C', 'N1RH', 'N2T_C', 'N2RH', 'D1', '']
    

test_guess_header()

# %%
def test_load_data_Hydroinnova_A(    
    folder="mock_data/test_dir",
    prefix="CRS03_Data",
):
    # Get list of files
    files = collect_files_from_folder(folder)
    # Select certain files
    files_filtered = filter_files(files, prefix=prefix, verbose=False)
    # Merge all files into one string
    data_str = merge_files(folder, files_filtered, verbose=False)
    # Guess header from first file
    column_names = guess_header(folder, files_filtered[0])
    # Convert string to DataFrame
    data = make_dataframe(data_str, column_names)
    assert isinstance(data, pandas.DataFrame)
    # Generate a Datetime column
    data = make_datetime(data, columns=1)
    # Set column as index and clean it
    data = datetime_as_index(data)
    assert isinstance(data.index, pandas.core.indexes.datetimes.DatetimeIndex)
    # Convert the remaining columns to numeric
    data = dataframe_to_numeric(data)
    assert data.P1_mb.dtype.kind == "f"
    return(data)

data = test_load_data_Hydroinnova_A()
# data.P1_mb.plot()
    

# %%
