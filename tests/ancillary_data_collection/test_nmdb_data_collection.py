import pytest
import os
from cosmosbase.ancillary_data_collection.nmdb_data_collection import (
    DateTimeHandler,
    CacheHandler,
)


def test_standardize_date():
    assert DateTimeHandler.standardize_date("2024-01-23") == "2024-01-23"
    assert DateTimeHandler.standardize_date("23/01/2024") == "2024-01-23"
    assert DateTimeHandler.standardize_date("01-23-2024") == "2024-01-23"
    standardized_date = DateTimeHandler.standardize_date("invalid-date")
    assert (
        standardized_date is None
    ), "The method should return None for invalid date"


@pytest.fixture
def cache_handler():
    cache_dir = "test_cache_dir"
    station = "test_station"
    handler = CacheHandler(cache_dir, station)
    # Setup before yield
    yield handler
    # Teardown after yield
    if os.path.exists(cache_dir):
        os.rmdir(cache_dir)


def test_cache_file_exists(cache_handler):
    # Create a test file
    test_file_path = os.path.join(
        cache_handler.cache_dir, f"nmdb_{cache_handler.station}.csv"
    )
    open(test_file_path, "a").close()

    # Test if the file is correctly identified
    cache_handler.check_cache_file_exists()
    assert cache_handler.cache_exists

    # Clean up
    os.remove(test_file_path)


# Assert Cache Created

# Assert Cache deleted

# Assert if cache available does not download

# def test_download_data_to_cache(self):
#     """Test to check if it downloads data from NMDB correctly"""
#     nmdb = NMDBDataHandler(
#         station="JUNG", startdate="10/10/2014", enddate="10/10/2016"
#     )
#     collected_data = nmdb.collect_data()
