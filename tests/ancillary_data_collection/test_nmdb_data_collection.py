from cosmosbase.ancillary_data_collection.nmdb_data_collection import (
    NMDBDataHandler,
)


class TestNMDBDataHandler:
    # Assert date standardisation works
    def test_standardize_date_valid_input(self):
        """Test the standardize_date method with valid input."""
        nmdb = NMDBDataHandler()
        standardized_date = nmdb.standardize_date("01-01-2023")
        assert (
            standardized_date == "2023-01-01"
        ), "The date should be standardized to YYYY-mm-dd format"

    def test_standardize_date_valid_input2(self):
        """Test the standardize_date method with valid input."""
        nmdb = NMDBDataHandler()
        standardized_date = nmdb.standardize_date("2023/01/01")
        assert (
            standardized_date == "2023-01-01"
        ), "The date should be standardized to YYYY-mm-dd format"

    def test_standardize_date_invalid_input(self):
        """Test the standardize_date method with invalid input."""
        nmdb = NMDBDataHandler()
        standardized_date = nmdb.standardize_date("invalid-date")
        assert (
            standardized_date is None
        ), "The method should return None for invalid date formats"

    # Assert Cache Created

    # Assert Cache deleted

    # Assert if cache available does not download

    # def test_download_data_to_cache(self):
    #     """Test to check if it downloads data from NMDB correctly"""
    #     nmdb = NMDBDataHandler(
    #         station="JUNG", startdate="10/10/2014", enddate="10/10/2016"
    #     )
    #     collected_data = nmdb.collect_data()
