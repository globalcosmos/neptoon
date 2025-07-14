import requests
from datetime import datetime
import logging
import pandas as pd
from pathlib import Path
from io import StringIO
from dateutil import parser

from neptoon.columns import ColumnInfo
from neptoon.config.global_configuration import GlobalConfig
from neptoon.data_audit import log_key_step
from neptoon.logging import get_logger

core_logger = get_logger()

NMDB_REFERENCES = {
    "JUNG": 161,
    "SOPO": 308,
    "OULU": 108,
    "PSNM": 615,
    "MXCO": 227,
    "AATA": 157,
    "INVK": 111,
    "KIEL": 166,
}

NMDB_CUTOFF_RIGIDITIES = {
    "JUNG": 4.49,
    "SOPO": 0.0,
    "OULU": 0.619,
    "PSNM": 16.674,
    "MXCO": 7.495,
    "AATA": 6.018,
    "INVK": 0.186,
    "KIEL": 2.383,
}


class NMDBDataAttacher:
    """
    This is the core class that a user interacts with when wanting to
    attach data from the NMDB.eu database to a dataframe. It includes
    methods for configuring the NMDBConfig class which is then used by
    other classes for fetching and parsing data from the NMDB.eu API.

    TODO - add validation steps to ensure dataframe is correct format
    """

    def __init__(
        self,
        data_frame: pd.DataFrame,
        new_column_name=str(ColumnInfo.Name.INCOMING_NEUTRON_INTENSITY),
    ):
        """
        Initialisation parameters

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame which requires data to be attached. It must have a
            datetime index.
        new_column_name : str, optional
            column name for the new column were neutron count data is
            appended, by default "incoming_neutron_intensity"
        """
        self.data_frame = data_frame
        self._new_column_name = new_column_name

    @property
    def new_column_name(self):
        return self._new_column_name

    def configure(
        self,
        station: str,
        reference_value: int | None = None,
        resolution="60",
        nmdb_table="revori",
    ):
        start_date_from_data = self.data_frame.index[0]
        end_date_from_data = self.data_frame.index[-1]
        self.config = NMDBConfig(
            start_date_wanted=start_date_from_data,
            end_date_wanted=end_date_from_data,
            station=station,
            reference_value=reference_value,
            resolution=resolution,
            nmdb_table=nmdb_table,
        )

    def fetch_data(self):
        """
        Creates a NMDBDataHandler using the config and collects the data
        whilst storing it under self.tmp_data
        """
        handler = NMDBDataHandler(self.config)
        self.tmp_data = handler.collect_nmdb_data()

    def attach_data(self):
        """
        Attaches the data stored in self.tmp_data to self.data_frame.
        This occurs inplace.

        Raises
        ------
        ValueError
            When index of the data is not Datetime an error occurs
        """
        if self.config.reference_value is None:
            if self.config.station not in list(NMDB_REFERENCES.keys()):
                message = (
                    "NMDB station not supported for automatic "
                    "reference creation. Please choose one of: \n"
                    f"{list(NMDB_REFERENCES.keys())}"
                )
                core_logger.error(message)
                raise ValueError(message)
            else:
                self.config.reference_value = NMDB_REFERENCES[
                    self.config.station
                ]

        if not isinstance(self.tmp_data.index, pd.DatetimeIndex):
            raise ValueError("DataFrame source must have a DatetimeIndex.")

        mapped_data = self.tmp_data["count"].reindex(
            self.data_frame.index, method="nearest"
        )
        self.data_frame[self.new_column_name] = mapped_data
        self.data_frame[
            str(ColumnInfo.Name.REFERENCE_INCOMING_NEUTRON_VALUE)
        ] = self.config.reference_value

        self.data_frame[str(ColumnInfo.Name.NMDB_REFERENCE_STATION)] = (
            self.config.station
        )
        self.data_frame[
            str(ColumnInfo.Name.REFERENCE_MONITOR_CUTOFF_RIGIDITY)
        ] = NMDB_CUTOFF_RIGIDITIES[self.config.station]

    def return_data_frame(self):
        """
        Returns the DataFrame attached in the object.

        Returns
        -------
        pd.DataFrame
            The DataFrame
        """
        return self.data_frame


class DateTimeHandler:
    """
    Class that holds Date standardization methods.

    This class provides static methods for converting and standardizing
    date formats to a common format (YYYY-mm-dd) used throughout the
    NMDB data collection process.
    """

    @staticmethod
    def convert_string_to_standard_date(date_str):
        """
        Converts a string date to the standard format (YYYY-mm-dd).

        Parameters
        ----------
        date_str : str
            The date string to convert.

        Returns
        -------
        str or None
            The standardized date string in format (YYYY-mm-dd), or None
            if the input date string is not a recognizable date format.

        Raises
        ------
        ValueError
            If the input string cannot be parsed into a valid date.
        """
        try:
            parsed_date = parser.parse(date_str)
            standardized_date_str = parsed_date.strftime("%Y-%m-%d")
            return standardized_date_str

        except ValueError:
            logging.error(
                f"Error: '{date_str}' is not a recognizable date format."
            )
            return None

    @staticmethod
    def format_datetime_to_standard_string(date_datetime):
        """
        Converts a datetime or pd.Timestamp date to the standard format
        (YYYY-mm-dd)

        Parameters
        ----------
        date_datetime : datetime.datetime or pandas.Timestamp
            The datetime object to convert.

        Returns
        -------
        str or None The standardized date string in format (YYYY-mm-dd),
        or None if the input
            is not a datetime.datetime or pandas.Timestamp instance.

        """
        if isinstance(date_datetime, (datetime, pd.Timestamp)):
            return date_datetime.strftime("%Y-%m-%d")
        else:
            logging.error("Input is not a valid datetime object")
            return None

    @staticmethod
    def standardize_date_input(date_input):
        """
        Takes a date as input, checks type, and converts it to the
        standard format (YYYY-mm-dd)

        Parameters
        ----------
        date_input : str or pd.TimeStamp or datetime.datetime
            Input date to be converted

        Returns
        -------
        str
            String of the date as YYYY-mm-dd

        Raises
        ------
        ValueError
            Raise error when neither str or datetime is given
        """
        if isinstance(date_input, (datetime, pd.Timestamp)):
            logging.info("Date was given as a pandas.Timestamp")
            return DateTimeHandler.format_datetime_to_standard_string(
                date_input
            )
        elif isinstance(date_input, str):
            logging.info(f"Date was given as a string: {date_input}")
            return DateTimeHandler.convert_string_to_standard_date(date_input)
        else:
            logging.error(f"Invalid date format: {date_input}")
            raise ValueError(f"Invalid date format: {date_input}")


class NMDBConfig:
    """
    Configuration class for NMDB data retrieval and processing.

    This class encapsulates configuration settings required for NMDB
    data retrieval, including date ranges for data collection, station
    identification, cache management, and data resolution settings. It
    ensures that all components of the NMDB data collection module use
    consistent and standardized configuration parameters.

    Parameters
    ----------
    start_date_wanted : str
        Start date for data retrieval, formatted as 'YYYY-MM-DD'.
    end_date_wanted : str
        End date for data retrieval, formatted as 'YYYY-MM-DD'.
    station : str, optional
        NMDB station code from which data is retrieved. Defaults to
        'JUNG'.
    cache_dir : str or None, optional
        Path to the cache directory for storing retrieved data. If None,
        uses the default OS cache directory.
    nmdb_table : str, optional
        Specific NMDB table to query data from. Defaults to 'revori'.
    resolution : str, optional
        Resolution of the data in minutes. Defaults to '60'.
    cache_exists : bool, optional
        Indicates whether cached data exists for the given parameters.
        Defaults to False.
    cache_start_date : str or None, optional
        Start date of the available cached data, formatted as
        'YYYY-MM-DD'. None if no cache exists.
    cache_end_date : str or None, optional
        End date of the available cached data, formatted as
        'YYYY-MM-DD'. None if no cache exists.
    start_date_needed : str or None, optional
        Start date for which data needs to be fetched, considering
        cached data. None if all data is cached.
    end_date_needed : str or None, optional
        End date for which data needs to be fetched, considering cached
        data. None if all data is cached.

    """

    @log_key_step("station", "nmdb_table", "resolution")
    def __init__(
        self,
        start_date_wanted,
        end_date_wanted,
        station="JUNG",
        reference_value=None,
        cache_dir=None,
        nmdb_table="revori",
        resolution="60",
        cache_exists=False,
        cache_start_date=None,
        cache_end_date=None,
        start_date_needed=None,
        end_date_needed=None,
    ):
        self._start_date_wanted = start_date_wanted
        self._end_date_wanted = end_date_wanted
        self._cache_dir = cache_dir
        self.station = station if station is not None else "JUNG"
        self.reference_value = reference_value
        self.nmdb_table = nmdb_table if nmdb_table is not None else "revori"
        self.resolution = resolution if resolution is not None else "60"
        self.cache_exists = cache_exists
        self.cache_start_date = cache_start_date
        self.cache_end_date = cache_end_date
        self.start_date_needed = start_date_needed
        self.end_date_needed = end_date_needed

    @property
    def start_date_wanted(self):
        return DateTimeHandler.standardize_date_input(self._start_date_wanted)

    @start_date_wanted.setter
    def start_date_wanted(self, value):
        self._start_date_wanted = DateTimeHandler.standardize_date_input(value)

    @property
    def end_date_wanted(self):
        return DateTimeHandler.standardize_date_input(self._end_date_wanted)

    @end_date_wanted.setter
    def end_date_wanted(self, value):
        self._end_date_wanted = DateTimeHandler.standardize_date_input(value)

    @property
    def cache_dir(self):
        GlobalConfig.create_cache_dir()
        if self._cache_dir is not None:
            return self._cache_dir
        else:
            return GlobalConfig.get_cache_dir()


class CacheHandler:
    """
    Class to handle cache management using downloaded NMDB data

    The cache handler managed file paths, naming of files, storage and
    deletion of the cache. As default it will be stored in the usual
    operating system cache location.

    Parameters
    ----------
    config : NMDBConfig
        An instance of the NMDBConfig class containing configuration
        settings

    Attributes
    ----------
    config : NMDBConfig
        Stores the configuration settings for NMDB data retrieval.
    _cache_file_path : Path or None
        The file path to the cache file, dynamically determined based on
        the NMDBConfig settings.

    Methods
    -------
    update_cache_file_path()
        Updates the cache file path based on the current NMDBConfig
        settings.
    check_cache_file_exists()
        Checks for the existence of the cache file and updates the
        configuration accordingly.
    read_cache()
        Reads the cached NMDB data from the file and returns it as a
        DataFrame.
    write_cache(cache_df)
        Writes a DataFrame to the cache file location.
    delete_cache()
        Deletes the cache file associated with the current NMDBConfig
        settings.
    check_cache_range()
        Determines the range of dates available in the cache and updates
        the NMDBConfig settings.

    Examples
    --------
    >>> config = NMDBConfig(start_date_wanted='2023-01-01',
    >>>             end_date_wanted='2023-01-31', station='JUNG')
    >>> cache_handler = CacheHandler(config)
    >>> cache_handler.update_cache_file_path()
    >>> print(cache_handler.cache_file_path)
    """

    def __init__(self, config):
        self.config = config
        self._cache_file_path = None
        self.update_cache_file_path()

    def update_cache_file_path(self):
        """Update the cache file path based on the current configuration."""
        self._cache_file_path = (
            Path(self.config.cache_dir)
            / f"nmdb_{self.config.station}_resolution_{self.config.resolution}"
            f"_nmdbtable_{self.config.nmdb_table}.csv"
        )

    @property
    def cache_file_path(self):
        return self._cache_file_path

    @cache_file_path.setter
    def cache_file_path(self, value):
        self._cache_file_path = value

    def check_cache_file_exists(self):
        """
        Checks the existence of the cache file and sets the property in
        config

        Returns
        -------
        None
        """
        if self.cache_file_path.exists():
            self.config.cache_exists = True

    def read_cache(self):
        """
        Reads cache nmdb file and formats index

        Returns
        -------
        df : pd.DataFrame
            DataFrame from the cache file
        """
        if self.config.cache_exists:
            df = pd.read_csv(self.cache_file_path)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)
            if df.index.tzinfo is None:
                df.index = df.index.tz_localize("UTC")
            else:
                df.index = df.index.tz_convert("UTC")
            return df

    def write_cache(self, cache_df):
        """
        Write NMDB data to the cache location using the cache_file_path
        attribute as a name.

        Parameters
        ----------
        cache_df : pd.DataFrame

        Returns
        -------
        None
        """
        if cache_df.empty:
            logging.warning("Attempting to write an empty DataFrame to cache.")
            return
        cache_df.to_csv(self.cache_file_path)

    def delete_cache(self):
        """
        Delete the cache file related to the current instance. E.g. if
        downloading hourly data for JUNG it will delete the file
        associated with hourly JUNG from the cache.

        Return
        ------
        None
        """
        if self.cache_file_path.exists():
            self.cache_file_path.unlink(missing_ok=True)
        logging.info("Cache file deleted")
        self.config.cache_exists = False

    def check_cache_range(self):
        """
        Function to find the range of data already available in the
        cache. It updates the config file depending on availability. It
        will either declare none existance of the cache, or update the
        start and end date of the cache.

        Returns
        -------
        None
        """
        self.check_cache_file_exists()
        if self.config.cache_exists:
            df_cache = self.read_cache()
            self.config.cache_start_date = df_cache.index.min().date()
            self.config.cache_end_date = df_cache.index.max().date()
        else:
            logging.info("There is no Cache file")
            self.config.cache_exists = False


class DataFetcher:
    """
    Class to handle sending external requests and fetching data.

    Parameters
    ----------
    config : NMDBConfig
        An instance of the configuration file.

    Methods
    -------
    get_ymd_from_date(date)
        static method which parses the date into seperate values to
        represent year, month and day
    create_nmdb_url()
        creates the url to request data from NMDB.eu, based on values in
        the configuration file
    fetch_data_http()
        uses the created url to request data from NMDB.eu and returns
        the text from the response
    parse_http_date(raw_data)
        uses the returned text from fetch_data_http() and parses it into
        a standard format. The format is a pd.Dataframe with a
        datetime.datetime index

    """

    def __init__(self, config):
        self.config = config

    @staticmethod
    def get_ymd_from_date(date):
        """
        Parses a given date into year, month, and day.

        Parameters
        ----------
        date : datetime or str
            The date to be parsed.

        Returns
        -------
        tuple
            Tuple containing the year, month, and day of the date.
        """
        standardized_date = str(
            DateTimeHandler.standardize_date_input(str(date))
        )
        year, month, day = standardized_date.split("-")
        return year, month, day

    def create_nmdb_url(self):
        """
        Creates the URL for obtaining the data using HTTP

        Returns
        -------
        url : str
            URL as a string
        """
        if self.config.start_date_needed is None:
            self.config.start_date_needed = self.config.start_date_wanted
        if self.config.end_date_needed is None:
            self.config.end_date_needed = self.config.end_date_wanted
        sy, sm, sd = self.get_ymd_from_date(self.config.start_date_needed)
        ey, em, ed = self.get_ymd_from_date(self.config.end_date_needed)

        nmdb_form = "wget"
        url = (
            f"https://www.nmdb.eu/nest/draw_graph.php?{nmdb_form}=1"
            f"&stations[]={self.config.station}"
            f"&tabchoice={self.config.nmdb_table}"
            f"&dtype=corr_for_efficiency"
            f"&tresolution={self.config.resolution}"
            f"&yunits=0&date_choice=bydate"
            f"&start_day={sd}&start_month={sm}&start_year={sy}"
            f"&start_hour=0&start_min=0&end_day={ed}&end_month={em}"
            f"&end_year={ey}&end_hour=23&end_min=59&output=ascii"
        )
        return url

    def fetch_data_http(self):
        """
        Fetches the data using http from NMDB.eu and processes it

        Returns
        -------
        Text : str
            Returns the text from the http site
        """
        url = self.create_nmdb_url()
        response = requests.get(url)
        response.raise_for_status()

        return response.text

    def parse_http_data(self, raw_data):
        """
        Parse the HTTP response data into a dataframe

        Parameters
        ----------
        raw_data : str
            The raw text file collected from NMDB.eu

        Returns
        -------
        pd.DataFrame
            A DataFrame with index DateTime and Counts per second

        Raises
        ------
        ValueError
            Raised if the requested date is not available at the
            specified NMDB station, indicated by a specific error
            message in the raw data.
        requests.exceptions.RequestException
            Raised if there's an issue parsing the HTTP response into a
            DataFrame, such as an incorrect format or network-related
            errors during the fetch.

        Examples
        --------
        Assuming an instance `nmdb_data_handler` of a class that
        includes this method:

        >>> df = nmdb_data_handler.fetch_and_parse_http_data()
        >>> print(df.head())

        """
        # if date has not been covered we raise an error
        if str(raw_data)[4:9] == "Sorry":
            raise ValueError(
                "Request date is not avalaible at ",
                self.config.station,
                " station, try other Neutron Monitoring station",
            )
        data = StringIO(raw_data)
        try:
            data = pd.read_csv(data, delimiter=";", comment="#")
            data.columns = ["count"]
            data.index.name = "datetime"
            data.index = pd.to_datetime(data.index).tz_localize("UTC")
            data.index = pd.to_datetime(data.index)
        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP Request failed: {e}")
        except ValueError as e:
            logging.error(e)
        return data

    def fetch_and_parse_http_data(self):
        """
        Fetches raw NMDB data via HTTP and parses it into a pandas
        DataFrame.

        This method combines the functionalities of fetching NMDB data
        from the designated HTTP source and subsequently parsing that
        raw data into a structured DataFrame. It leverages
        `fetch_data_http` to retrieve the data and `parse_http_data` to
        transform it into a usable format.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the NMDB data, indexed by datetime
            with counts per second.

        Raises
        ------
        Refer to documentation for fetch_data_http() and
        parse_http_data()

        Examples
        --------
        Assuming an instance `nmdb_data_handler` of a class that
        includes this method:

        >>> df = nmdb_data_handler.fetch_and_parse_http_data()
        >>> print(df.head())
        """
        raw_data = self.fetch_data_http()
        return self.parse_http_data(raw_data)


class DataManager:
    """
    Manages the integration of cached and newly fetched NMDB data.

    This class is responsible for determining the necessity of fetching
    new NMDB data based on the existing cache and the desired date
    range. It also handles the combination of cached data with newly
    fetched data to provide a complete dataset for analysis.

    Parameters
    ----------
    config : NMDBConfig
        Configuration settings for NMDB data retrieval.
    cache_handler : CacheHandler
        Handles operations related to caching of NMDB data.
    data_fetcher : DataFetcher
        Responsible for fetching new data from NMDB.

    Attributes
    ----------
    need_data_before_cache : bool or None
        Indicates if data before the cached range is needed.
    need_data_after_cache : bool or None
        Indicates if data after the cached range is needed.

    Methods
    -------
    check_if_need_extra_data()
        Evaluates the need for fetching data outside the current cache
        range.
    set_dates_for_nmdb_download()
        Updates the configuration with the date ranges that need to be
        fetched.
    combine_cache_and_new_data(df_cache, df_download)
        Merges newly fetched data with existing cached data, ensuring no
        duplication.

    """

    def __init__(self, config, cache_handler, data_fetcher):
        """
        Initializes the DataManager with the given configuration, cache
        handler, and data fetcher.

        Parameters
        ----------
        config : NMDBConfig
            Configuration settings for NMDB data retrieval.
        cache_handler : CacheHandler
            Handles operations related to caching of NMDB data.
        data_fetcher : DataFetcher
            Responsible for fetching new data from NMDB.
        """

        self.config = config
        self.cache_handler = cache_handler
        self.data_fetcher = data_fetcher
        self.need_data_before_cache = None
        self.need_data_after_cache = None

    def check_if_need_extra_data(self):
        """
        Updates configuration instance with boolean values stating
        whether a download of data is required before or after the
        desired dates.

        Returns
        -------
        None
        """

        self.cache_handler.check_cache_range()
        start_date_wanted = pd.to_datetime(
            self.config.start_date_wanted
        ).date()
        end_date_wanted = pd.to_datetime(self.config.end_date_wanted).date()

        self.need_data_before_cache = (
            start_date_wanted < self.config.cache_start_date
        )
        self.need_data_after_cache = (
            end_date_wanted > self.config.cache_end_date
        )

    def set_dates_for_nmdb_download(self):
        """
        Updates the configuration instance with the download range for
        NMDB data based upon the desired data and the available data in
        the cache.

        Returns
        -------
        None
        """
        if self.need_data_before_cache and self.need_data_after_cache:
            self.config.start_date_needed = self.config.start_date_wanted
            self.config.end_date_needed = self.config.end_date_wanted

        elif self.need_data_before_cache:
            self.config.start_date_needed = self.config.start_date_wanted
            self.config.end_date_needed = self.config.cache_start_date

        elif self.need_data_after_cache:
            self.config.start_date_needed = self.config.cache_end_date
            self.config.end_date_needed = self.config.end_date_wanted

    def combine_cache_and_new_data(self, df_cache, df_download):
        """
        Combines cached and newly downloaded NMDB data into a single
        DataFrame, ensuring data continuity and no duplication.

        Parameters
        ----------
        df_cache : pd.DataFrame
            The DataFrame containing cached data.
        df_download : pd.DataFrame
            The DataFrame containing newly downloaded data.

        Returns
        -------
        pd.DataFrame
            The combined DataFrame, sorted by datetime.
        """
        if "datetime" not in df_cache.index.names:
            df_cache.set_index("datetime", inplace=True)
        if "datetime" not in df_download.index.names:
            df_download.index = df_download.index.tz_localize("UTC")

        if df_cache.index.tz is None:
            df_cache.index = df_cache.index.tz_localize("UTC")
        if df_download.index.tz is None:
            df_download.index = df_download.index.tz_localize("UTC")

        combined_df = pd.concat([df_cache, df_download])
        combined_df.reset_index(inplace=True)
        combined_df.drop_duplicates(
            subset="datetime", keep="first", inplace=True
        )
        combined_df.set_index("datetime", inplace=True)
        combined_df_sorted = combined_df.sort_index()
        return combined_df_sorted


class NMDBDataHandler:
    """
    Handles the retrieval and management of NMDB data.

    This class integrates the `CacheHandler`, `DataFetcher`, and
    `DataManager` to manage NMDB data. It ensures that data is fetched
    from the NMDB source only when necessary, preferring cached data to
    minimize network requests. The class handles cases where new data
    needs to be fetched either because it's not present in the cache or
    only partial data is available.

    Parameters
    ----------
    config : NMDBConfig
        Configuration settings for NMDB data retrieval, including
        desired date ranges, station information, and caching
        preferences.

    Attributes
    ----------
    config : NMDBConfig
        Stores the provided NMDB configuration settings.
    cache_handler : CacheHandler
        Manages caching operations for NMDB data.
    data_fetcher : DataFetcher
        Responsible for fetching new NMDB data when required.
    data_manager : DataManager
        Determines the need for and manages the retrieval of new data
        based on cache status and configuration settings.

    Methods
    -------
    collect_nmdb_data()
        Retrieves NMDB data, prioritizing cached data and fetching new
        data as needed. Returns a DataFrame containing the relevant NMDB
        data.

    Examples
    --------
    >>> config = NMDBConfig(start_date_wanted='2023-01-01',
    >>>             end_date_wanted='2023-01-31', station='JUNG')
    >>> nmdb_handler = NMDBDataHandler(config)
    >>> nmdb_data = nmdb_handler.collect_nmdb_data()
    >>> print(nmdb_data.head())
    """

    def __init__(self, config):
        """
        Initializes the NMDBDataHandler with the given NMDBConfig instance.

        Parameters
        ----------
        config : NMDBConfig
            Configuration settings for NMDB data retrieval.
        """
        self.config = config
        self.cache_handler = CacheHandler(config)
        self.data_fetcher = DataFetcher(config)
        self.data_manager = DataManager(
            config, self.cache_handler, self.data_fetcher
        )

    def collect_nmdb_data(self):
        """
        Collects NMDB data based on the specified configuration, using
        cached data when available and fetching new data as necessary.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing NMDB data for the requested range.
            This may be a combination of cached and newly fetched data,
            or solely from one source, depending on availability.

        Examples
        --------
        Assuming `config` has been defined and passed to
        `NMDBDataHandler`:

        >>> nmdb_data = nmdb_handler.collect_nmdb_data()
        >>> print(nmdb_data.head())

        Note: This example assumes that `nmdb_handler` has been
        instantiated with a valid `NMDBConfig`.
        """

        self.cache_handler.check_cache_file_exists()
        if self.config.cache_exists:
            self.cache_handler.check_cache_range()
            self.data_manager.check_if_need_extra_data()
            if (
                self.data_manager.need_data_before_cache is False
                and self.data_manager.need_data_after_cache is False
            ):
                core_logger.info("All data is present in the cache.")
                df_cache = self.cache_handler.read_cache()
                return df_cache

            else:
                self.data_manager.set_dates_for_nmdb_download()
                df_cache = self.cache_handler.read_cache()
                df_download = self.data_fetcher.fetch_and_parse_http_data()
                df_combined = self.data_manager.combine_cache_and_new_data(
                    df_cache, df_download
                )
                self.cache_handler.write_cache(df_combined)
                return df_combined
        else:
            core_logger.info(
                f"No cache file found at"
                f" {self.cache_handler.cache_file_path}."
            )
            df_download = self.data_fetcher.fetch_and_parse_http_data()
            self.cache_handler.write_cache(df_download)
            self.config.cache_exists = True
            self.cache_handler.cache_file = df_download
            return df_download
