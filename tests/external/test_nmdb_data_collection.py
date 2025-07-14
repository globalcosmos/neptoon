import pandas as pd
import requests
import pandas.testing as pdt
from pathlib import Path
from neptoon.external.nmdb_data_collection import (
    DateTimeHandler,
    NMDBConfig,
    NMDBDataHandler,
    DataFetcher,
    CacheHandler,
    DataManager,
)

"""
DateTimeHandler Tests
"""


def test_standardize_date_input():
    """Tests to ensure teh standardize date works"""
    assert DateTimeHandler.standardize_date_input("2024-01-23") == "2024-01-23"
    assert DateTimeHandler.standardize_date_input("23/01/2024") == "2024-01-23"
    assert DateTimeHandler.standardize_date_input("01-23-2024") == "2024-01-23"
    assert (
        DateTimeHandler.standardize_date_input(pd.Timestamp("2024-01-23"))
        == "2024-01-23"
    )
    assert DateTimeHandler.standardize_date_input(pd.to_datetime("2024-01-23"))
    standardized_date = DateTimeHandler.standardize_date_input("invalid-date")
    assert (
        standardized_date is None
    ), "The method should return None for invalid date"


"""
CacheHandler Tests
"""


def test_read_cache():
    """Test the read cache and make sure the format is as expected"""
    config = NMDBConfig(
        start_date_wanted="2015-10-10",
        end_date_wanted="2016-10-10",
    )
    cache_handler = CacheHandler(config)
    mock_file_path = (
        Path(__file__).parent / "mock_data" / "example_cache_1516.csv"
    )
    # monkeypatch.setattr(config, "cache_exists", True)
    config.cache_exists = True
    cache_handler.cache_file_path = mock_file_path
    df = cache_handler.read_cache()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "count" in df.columns
    assert isinstance(df.index, pd.DatetimeIndex)


def test_check_cache_range():
    """Test on logic to collect cache range"""
    config = NMDBConfig(
        start_date_wanted="2015-10-10",
        end_date_wanted="2016-10-10",
    )
    cache_handler = CacheHandler(config)
    mock_file_path = (
        Path(__file__).parent / "mock_data" / "example_cache_1516.csv"
    )
    config.cache_exists = True
    cache_handler.cache_file_path = mock_file_path
    cache_handler.check_cache_range()
    df = pd.read_csv(mock_file_path)
    df["datetime"] = pd.to_datetime(df["datetime"])

    assert config.cache_start_date == df["datetime"].min().date()
    assert config.cache_end_date == df["datetime"].max().date()


"""
DataFetcher Tests
"""


def test_get_ymd_from_date(monkeypatch):
    """Test the ymd parsing step in DataFetcher"""
    monkeypatch.setattr(
        DateTimeHandler, "standardize_date_input", lambda x: "2016-10-28"
    )
    config = NMDBConfig(
        start_date_wanted="2015-10-10",
        end_date_wanted="2016-10-10",
    )
    data_fetcher = DataFetcher(config)
    year, month, day = data_fetcher.get_ymd_from_date("some_date")

    assert year == "2016"
    assert month == "10"
    assert day == "28"


def test_create_nmdb_url_config1(monkeypatch):
    """Test the creation of the NMDB http URL"""

    def mock_get_ymd_from_date(date1, date2):
        return ("2015", "10", "10")

    config = NMDBConfig(
        start_date_wanted="2015-10-10",
        end_date_wanted="2015-10-10",
        station="JUNG",
        nmdb_table="revori",
        resolution="60",
        start_date_needed=None,
        end_date_needed=None,
    )

    monkeypatch.setattr(
        DataFetcher, "get_ymd_from_date", mock_get_ymd_from_date
    )

    data_fetcher = DataFetcher(config)
    expected_url = (
        "https://www.nmdb.eu/nest/draw_graph.php?wget=1&stations"
        "[]=JUNG&tabchoice=revori&dtype=corr_for_efficiency"
        "&tresolution=60&yunits=0&date_choice=bydate"
        "&start_day=10&start_month=10&start_year=2015&start_hour=0"
        "&start_min=0&end_day=10&end_month=10&end_year=2015"
        "&end_hour=23&end_min=59&output=ascii"
    )
    url = data_fetcher.create_nmdb_url()
    assert url == expected_url


class MockHTTPResponse:
    def __init__(self, text_data):
        self.text = text_data

    def raise_for_status(self):
        pass


def test_fetch_data_http(monkeypatch):
    """Test fetching data from http server with mock http"""
    file_location = (
        Path(__file__).parent / "mock_data" / "mock_http_2015_2016.txt"
    )

    text_to_assert = """#        STATION: JUNG
#     START TIME: 2015-10-10 00:00:00 UTC
#       END TIME: 2016-10-10 23:00:00 UTC
#     NMDB TABLE: revised original
#    REV EQ. ORI: No
#    REV. VALUES: 4543"""

    config = NMDBConfig(
        start_date_wanted="2015-10-10",
        end_date_wanted="2016-10-10",
    )

    def mock_get(*args, **kwargs):
        with open(
            file_location,
            "r",
        ) as file:
            mock_text = file.read()
        return MockHTTPResponse(mock_text)

    monkeypatch.setattr(requests, "get", mock_get)

    handler = NMDBDataHandler(config)

    result = handler.data_fetcher.fetch_data_http()
    assert text_to_assert in result


def test_parse_http_date():
    config = NMDBConfig(
        start_date_wanted="2015-10-10",
        end_date_wanted="2015-10-10",
        station="JUNG",
    )
    mock_file_path = (
        Path(__file__).parent / "mock_data" / "mock_http_2015_2016.txt"
    )
    assert_file_path = (
        Path(__file__).parent / "mock_data" / "example_cache_1516.csv"
    )

    df_to_compare = pd.read_csv(assert_file_path)
    df_to_compare["datetime"] = pd.to_datetime(df_to_compare["datetime"])
    df_to_compare.set_index("datetime", inplace=True)
    df_to_compare.index = df_to_compare.index.tz_localize("UTC")

    data_fetcher = DataFetcher(config)
    with open(mock_file_path, "r") as file:
        raw_data = file.read()

    data = data_fetcher.parse_http_data(raw_data)

    pdt.assert_frame_equal(data, df_to_compare)


"""
DataManager Tests
"""


def test_check_if_need_extra_data(monkeypatch):
    """Test to check logic on whether extra dates are needed"""
    config = NMDBConfig(
        start_date_wanted="2015-10-10",
        end_date_wanted="2016-10-10",
    )
    monkeypatch.setattr(CacheHandler, "check_cache_range", lambda x: None)
    cache_handler = CacheHandler(config)
    data_fetcher = DataFetcher(config)
    data_manager = DataManager(config, cache_handler, data_fetcher)
    config.cache_start_date = pd.to_datetime("2015-10-10").date()
    config.cache_end_date = pd.to_datetime("2016-10-10").date()

    data_manager.check_if_need_extra_data()

    assert data_manager.need_data_before_cache is False
    assert data_manager.need_data_after_cache is False

    config.cache_start_date = pd.to_datetime("2015-11-10").date()
    config.cache_end_date = pd.to_datetime("2016-10-10").date()

    data_manager.check_if_need_extra_data()

    assert data_manager.need_data_before_cache is True
    assert data_manager.need_data_after_cache is False

    config.cache_start_date = pd.to_datetime("2015-11-10").date()
    config.cache_end_date = pd.to_datetime("2016-09-10").date()

    data_manager.check_if_need_extra_data()

    assert data_manager.need_data_before_cache is True
    assert data_manager.need_data_after_cache is True

    config.cache_start_date = pd.to_datetime("2015-11-10").date()
    config.cache_end_date = pd.to_datetime("2016-09-10").date()

    data_manager.check_if_need_extra_data()

    assert data_manager.need_data_before_cache is True
    assert data_manager.need_data_after_cache is True


def test_combine_cache_and_new_data(monkeypatch):
    config = NMDBConfig(
        start_date_wanted="2015-10-10",
        end_date_wanted="2016-10-10",
    )
    cache_handler = CacheHandler(config)
    data_fetcher = DataFetcher(config)
    data_manager = DataManager(config, cache_handler, data_fetcher)

    df_cache_path = (
        Path(__file__).parent / "mock_data" / "example_cache_merge1.csv"
    )
    df_cache = pd.read_csv(df_cache_path)
    df_cache["datetime"] = pd.to_datetime(df_cache["datetime"])
    df_cache.set_index("datetime", inplace=True)

    print(df_cache_path)

    df_download_path = (
        Path(__file__).parent / "mock_data" / "example_cache_merge2.csv"
    )
    df_download = pd.read_csv(df_download_path)
    df_download["datetime"] = pd.to_datetime(df_download["datetime"])
    df_download.set_index("datetime", inplace=True)

    print(df_download_path)

    df_assert_path = (
        Path(__file__).parent / "mock_data" / "example_cache_merge_assert.csv"
    )
    df_assert = pd.read_csv(df_assert_path)
    df_assert["datetime"] = pd.to_datetime(df_assert["datetime"])
    df_assert.set_index("datetime", inplace=True)
    df_assert.index = df_assert.index.tz_localize("UTC")

    combined_df = data_manager.combine_cache_and_new_data(
        df_cache, df_download
    )

    assert isinstance(combined_df, pd.DataFrame)
    assert not combined_df.empty
    assert "count" in combined_df.columns
    pdt.assert_frame_equal(combined_df, df_assert)


# TODO:
# NMDBDataHandler Tests - canary
