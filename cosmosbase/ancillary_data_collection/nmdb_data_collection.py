import os
import time
import requests
import logging
import pandas as pd
from bs4 import BeautifulSoup
import urllib
from io import StringIO
from dateutil import parser
import cosmosbase.configuration.config as cfg


def timed_function(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(
            f"Function '{func.__name__}' took {end_time - start_time} seconds to run."
        )
        return result

    return wrapper


class DateTimeHandler:
    @staticmethod
    def convert_string_to_standard_date(date_str):
        """Function to standardize dates given as a string

        Parameters
        ----------
        date_str : str
            Converts a string date to the standard format (YYYY-mm-dd)

        Returns
        -------
        str
            Date string in format (YYYY-mm-dd)
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
        """Standardize dates given as a pd.DateTime

        Parameters
        ----------
        date_datetime : pd.Datetime

        Returns
        -------
        Str: Formatted Datetime

        """
        return date_datetime.strftime("%Y-%m-%d")

    @staticmethod
    def standardize_date_input(date_input):
        """Checks datetime input type and converts it to the standard
            format: YYYY-mm-dd
        Parameters
        ----------
        date_input : str or DateTime
            Input date

        Returns
        -------
        Str
            String of the date as YYYY-mm-dd

        Raises
        ------
        ValueError
            Raise error when neither str or datetime is given
        """
        if isinstance(date_input, pd.Timestamp):
            logging.info("Date was given as a pd.Timestamp")
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
    """Config class for shared attributes in NMDB process."""

    def __init__(
        self,
        start_date_wanted,
        end_date_wanted,
        station="JUNG",
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
        self._station = station
        self._nmdb_table = nmdb_table
        self._resolution = resolution
        self._cache_exists = cache_exists
        self._cache_start_date = cache_start_date
        self._cache_end_date = cache_end_date
        self._start_date_needed = start_date_needed
        self._end_date_needed = end_date_needed

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
        cfg.GlobalConfig.create_cache_dir()
        if self._cache_dir is not None:
            return self._cache_dir
        else:
            return cfg.GlobalConfig.get_cache_dir()

    @property
    def station(self):
        return self._station

    @property
    def nmdb_table(self):
        return self._nmdb_table

    @property
    def resolution(self):
        return self._resolution

    @property
    def cache_exists(self):
        return self._cache_exists

    @cache_exists.setter
    def cache_exists(self, value):
        self._cache_exists = value

    @property
    def cache_start_date(self):
        return self._cache_start_date

    @cache_start_date.setter
    def cache_start_date(self, value):
        self._cache_start_date = value

    @property
    def cache_end_date(self):
        return self._cache_end_date

    @cache_end_date.setter
    def cache_end_date(self, value):
        self._cache_end_date = value

    @property
    def start_date_needed(self):
        return self._start_date_needed

    @start_date_needed.setter
    def start_date_needed(self, value):
        self._start_date_needed = value

    @property
    def end_date_needed(self):
        return self._end_date_needed

    @end_date_needed.setter
    def end_date_needed(self, value):
        self._end_date_needed = value


class CacheHandler:
    """CacheHandler is the object that handles reading, writing,
    deleting and checking existance of the cache.
    """

    def __init__(self, config):
        self.config = config
        self._cache_file_path = None
        # self._cache_file = None

    @property
    def cache_file_path(self):
        self._cache_file_path = os.path.join(
            self.config.cache_dir,
            f"nmdb_{self.config.station}_resolution_{self.config.resolution}"
            f"_nmdbtable_{self.config.nmdb_table}.csv",
        )
        return self._cache_file_path

    # @property
    # def cache_file(self):
    #     if self.config.cache_exists:
    #         self._cache_file = self.read_cache()

    # @cache_file.setter
    # def cache_file(self, newcache):
    #     self._cache_file = newcache

    def check_cache_file_exists(self):
        """Checks the existence of the cache file
        and sets property in config

        Returns
        -------
        Boolean
            True/False is there a cache file
        """

        if os.path.exists(self.cache_file_path):
            self.config.cache_exists = True

    def read_cache(self):
        """Reads cache nmdb file and formats index

        Returns
        -------
        DataFrame
            DF of the cache file
        """
        if self.config.cache_exists:
            try:
                df = pd.read_csv(self.cache_file_path)
                df["datetime"] = pd.to_datetime(df["datetime"])
                df.set_index("datetime", inplace=True)
                return df
            except FileNotFoundError:
                logging.error("Cache file not found.")
                return None
        else:
            logging.error("Cache file does not exist")

    def write_cache(self, cache_df):
        """Write NMDB data to the cache location

        Parameters
        ----------
        cache_df : DataFrame
        """
        if cache_df.empty:
            logging.warning("Attempting to write an empty DataFrame to cache.")
            return
        cache_df.to_csv(self.cache_file_path)

    def delete_cache(self):
        """Delete the cache file assigne to the current instance. E.g.
        if downloading data for JUNG it will delete the file
        associated with JUNG from the cache
        """
        try:
            os.remove(self.cache_file_path)
            logging.info("Cache file deleted")
            self.config.cache_exists = False
        except FileNotFoundError:
            logging.error("Cache file not found when attempting to delete.")

    def check_cache_range(self):
        """Function to find the range of data already available in the
        cache
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
    """Class concerned with requesting data from NMDB.eu"""

    def __init__(self, config):
        self.config = config

    @staticmethod
    def get_ymd_from_date(date):
        """Parses a given date into year, month, and day.

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

    def create_nmdb_url(self, method="http"):
        """Creates the URL for obtaining the data using HTTP

        Parameters
        ----------
        method : str, optional
            Decide whether to use HTTP or HTML for collection, by
            default "http"

        Returns
        -------
        str
            URL as a string
        """
        if self.config.start_date_needed == None:
            self.config.start_date_needed = self.config.start_date_wanted
        if self.config.end_date_needed == None:
            self.config.end_date_needed = self.config.end_date_wanted
        sy, sm, sd = self.get_ymd_from_date(self.config.start_date_needed)
        ey, em, ed = self.get_ymd_from_date(self.config.end_date_needed)

        if method == "http":
            nmdb_form = "wget"
        elif method == "html":
            nmdb_form = "formchk"
        url = (
            f"http://nest.nmdb.eu/draw_graph.php?{nmdb_form}=1"
            f"&stations[]={self.config.station}"
            f"&tabchoice={self.config.nmdb_table}"
            f"&dtype=corr_for_efficiency"
            f"&tresolution={self.config.resolution}"
            f"&force=1&yunits=0&date_choice=bydate"
            f"&start_day={sd}&start_month={sm}&start_year={sy}"
            f"&start_hour=0&start_min=0&end_day={ed}&end_month={em}"
            f"&end_year={ey}&end_hour=23&end_min=59&output=ascii"
        )
        return url

    def fetch_data_http(self):
        """Fetches the data using http from NMDB.eu and processes it

        Returns
        -------
        DataFrame
            DataFrame of data
        """
        url = self.create_nmdb_url(method="http")
        response = requests.get(url)
        response.raise_for_status()

        return response.text

    def parse_http_data(self, raw_data):
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
            data.index = pd.to_datetime(data.index)
        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP Request failed: {e}")
            return None
        except ValueError as e:
            logging.error(e)
            return None
        except pd.errors.ParserError as e:
            logging.error(f"Error parsing data into DataFrame: {e}")
            return None
        return data

    def fetch_and_parse_http_data(self):
        raw_data = self.fetch_data_http()
        return self.parse_http_data(raw_data)

    def fetch_data_html(self):
        """Fetches data using html from NMDB.eu

        Returns
        -------
        DataFrame
            DataFrame of data
        """
        url = self.create_nmdb_url(method="html")

        # Fetch and read the HTML content
        response = urllib.request.urlopen(url)
        html = response.read()

        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html, features="html.parser")
        pre = soup.find("pre").text

        # Extract and process data from the <pre> tag
        data = pre[pre.find("start_date_time") :].replace(
            "start_date_time   1HCOR_E", ""
        )
        lines = data.strip().split("\n")[1:]  # Skip header line

        # Create DataFrame from the processed lines
        dfneut = pd.DataFrame(
            [line.split(";") for line in lines], columns=["datetime", "count"]
        )
        dfneut.set_index("datetime", inplace=True)

        return dfneut


class DataManager:
    """Class for managing the data collected from cache and online"""

    def __init__(self, config, cache_handler, data_fetcher):
        self.config = config
        self.cache_handler = cache_handler
        self.data_fetcher = data_fetcher
        self.need_data_before_cache = None
        self.need_data_after_cache = None

    def check_if_need_extra_data(self):
        """Boolean on whether data is needed before or after"""
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
        """Appends new data to cached data and sorts by date.

        Args:
            df_cache (DataFrame): The cached data.
            dfdownload (DataFrame): The newly downloaded data.

        Returns:
            DataFrame: The combined and sorted DataFrame.
        """
        if "datetime" not in df_cache.index.names:
            df_cache.set_index("datetime", inplace=True)
        if "datetime" not in df_download.index.names:
            df_download.set_index("datetime", inplace=True)

        combined_df = pd.concat([df_cache, df_download])
        combined_df.reset_index(inplace=True)
        combined_df.drop_duplicates(
            subset="datetime", keep="first", inplace=True
        )
        combined_df.set_index("datetime", inplace=True)
        combined_df_sorted = combined_df.sort_index()
        return combined_df_sorted


class NMDBDataHandler:
    """Overall handler for NMDB functions. Takes the classes and pieces
    them together to collect data from NMDB. If data is available in the
    cache it will avoid sending requests to server, if partial data is
    available it will download what is needed
    """

    def __init__(
        self,
        config,
    ):
        """
        Initialize the NMDBDataHandler Class.

        Parameters
        ----------
        start_date : str
            The start date for data collection.
        end_date : str
            The end date for data collection.
        station : str, optional
            The station to collect data from, defaults to "JUNG".
        initializer : NMDBinitializer, optional
            An instance of NMDBinitializer to create necessary components.
        """
        self.config = config
        self.cache_handler = CacheHandler(config)
        self.data_fetcher = DataFetcher(config)
        self.data_manager = DataManager(
            config, self.cache_handler, self.data_fetcher
        )

    def collect_nmdb_data(self):
        """Wrapper function to collect nmdb data using the supplied info"""
        self.cache_handler.check_cache_file_exists()
        if self.config.cache_exists:
            self.cache_handler.check_cache_range()
            self.data_manager.check_if_need_extra_data()
            if (
                self.data_manager.need_data_before_cache == False
                and self.data_manager.need_data_after_cache == False
            ):
                logging.info("All data is present in the cache.")
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
            logging.info(
                f"No cache file found at"
                f" {self.cache_handler.cache_file_path}."
            )
            df_download = self.data_fetcher.fetch_and_parse_http_data()
            self.cache_handler.write_cache(df_download)
            self.config.cache_exists = True
            self.cache_handler.cache_file = df_download
            return df_download
