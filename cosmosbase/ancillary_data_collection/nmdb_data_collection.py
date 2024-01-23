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
    def standardize_date(date_str):
        """Function to standardize the date automatically

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


class CacheHandler:
    def __init__(self, cache_dir, station):
        self.cache_dir = cache_dir
        self.station = station
        self.cache_exists = False

    def check_cache_file_exists(self):
        cache_file_path = os.path.join(
            self.cache_dir, f"nmdb_{self.station}.csv"
        )
        if os.path.exists(cache_file_path):
            self.cache_exists = True
            return True

    def read_cache(self):
        """Read the cache file, fix index and return a DataFrame."""
        self.check_cache_file_exists()
        if self.cache_exists:
            filepath = os.path.join(self.cache_dir, f"nmdb_{self.station}.csv")
            try:
                df = pd.read_csv(filepath)
                df["DT"] = pd.to_datetime(df["DT"])
                df.set_index("DT", inplace=True)
                return df
            except FileNotFoundError:
                logging.error("Cache file not found.")
                return None
        else:
            logging.error("Cache file does not exist")

    def write_cache(self, cache_df):
        """Write a DataFrame to the cache file."""
        if cache_df.empty:
            logging.warning("Attempting to write an empty DataFrame to cache.")
            return
        filepath = os.path.join(self.cache_dir, f"nmdb_{self.station}.csv")
        cache_df.to_csv(filepath)

    def delete_cache(self):
        """Delete the cached file for the current instance."""
        filepath = os.path.join(self.cache_dir, f"nmdb_{self.station}.csv")
        try:
            os.remove(filepath)
            logging.info("Cache file deleted")
            self.cach_exists = False
        except FileNotFoundError:
            logging.error("Cache file not found when attempting to delete.")


class DataFetcher:
    def __init__(
        self,
        start_date,
        end_date,
        station="JUNG",
        resolution="60",
        nmdb_table="revori",
    ):
        self.station = station
        self.start_date = start_date
        self.end_date = end_date
        self.resolution = resolution
        self.nmdb_table = nmdb_table

    def create_nmdb_url(self, method="http"):
        # Split dates for use in URL
        sy, sm, sd = str(
            DateTimeHandler.standardize_date(str(self.start_date))
        ).split("-")
        ey, em, ed = str(
            DateTimeHandler.standardize_date(str(self.end_date))
        ).split("-")

        if method == "http":
            # Construct URL for data request
            url = (
                f"http://nest.nmdb.eu/draw_graph.php?wget=1"
                f"&stations[]={self.station}&tabchoice={self.nmdb_table}&"
                f"dtype=corr_for_efficiency"
                f"&tresolution={self.resolution}&force=1"
                f"&yunits=0&date_choice=bydate"
                f"&start_day={sd}&start_month={sm}&start_year={sy}"
                f"&start_hour=0&start_min=0&end_day={ed}&end_month={em}"
                f"&end_year={ey}&end_hour=23&end_min=59&output=ascii"
            )
        elif method == "html":
            # Construct URL for data request
            url = (
                f"http://nest.nmdb.eu/draw_graph.php?formchk=1"
                f"&stations[]={self.station}&tabchoice={self.nmdb_table}&"
                f"dtype=corr_for_efficiency"
                f"&tresolution={self.resolution}&force=1&yunits=0&date_choice=bydate"
                f"&start_day={sd}&start_month={sm}&start_year={sy}"
                f"&start_hour=0&start_min=0&end_day={ed}&end_month={em}"
                f"&end_year={ey}&end_hour=23&end_min=59&output=ascii"
            )
        return url

    def fetch_data_http(self):
        url = self.create_nmdb_url(method="http")
        try:
            response = requests.get(url)
            response.raise_for_status()
            # if date has not been covered we raise an error
            if str(response.text)[4:9] == "Sorry":
                raise ValueError(
                    "Request date is not avalaible at ",
                    self.station,
                    " station, try other Neutron Monitoring station",
                )
            data = StringIO(response.text)
            data = pd.read_csv(data, delimiter=";", comment="#")
            data.columns = ["count"]
            data.index.name = "DT"
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

    def fetch_data_html(self):
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
            [line.split(";") for line in lines], columns=["DT", "count"]
        )
        dfneut.set_index("DT", inplace=True)

        return dfneut


class DataManager:
    def __init__(self, start_date, end_date, cache_dir, station):
        self.start_date = start_date
        self.end_date = end_date
        self.cache_dir = cache_dir
        self.station = station
        self.cache_handler = CacheHandler(cache_dir, station)
        self.need_data_before_cache = None
        self.need_data_after_cache = None

    def check_cache_range(self):
        df_cache = self.cache_handler.read_cache()
        # Get the date range in cache
        cached_start = df_cache.index.min()
        cached_end = df_cache.index.max()
        # Convert datetime objects to date for comparison
        self.cached_start_date = cached_start.date()
        self.cached_end_date = cached_end.date()

    def check_if_need_extra_data(self):
        start_date = pd.to_datetime(self.start_date).date()
        end_date = pd.to_datetime(self.end_date).date()

        self.need_data_before_cache = start_date < self.cached_start_date
        self.need_data_after_cache = end_date > self.cached_end_date

    def append_and_sort_data(self, df_cache, df_download):
        """Appends new data to cached data and sorts by date.

        Args:
            df_cache (DataFrame): The cached data.
            dfdownload (DataFrame): The newly downloaded data.

        Returns:
            DataFrame: The combined and sorted DataFrame.
        """
        # # Concatenate the two DataFrames
        # combined_df = pd.concat([df_cache, df_download])

        # # Sort the DataFrame by the index (DT)
        # combined_df_sorted = combined_df.sort_index()
        # # combined_df_sorted = combined_df.sort_values(by="DT")

        # # # Reset the index if necessary
        # # combined_df_sorted.reset_index(inplace=True)

        # return combined_df_sorted
        # Ensure 'DT' is set as index for both DataFrames
        if "DT" not in df_cache.index.names:
            df_cache.set_index("DT", inplace=True)
        if "DT" not in df_download.index.names:
            df_download.set_index("DT", inplace=True)

        # Concatenate the two DataFrames
        combined_df = pd.concat([df_cache, df_download])

        # Reset the index to work with the 'DT' column for deduplication
        combined_df.reset_index(inplace=True)

        # Drop duplicates (keeping the first occurrence)
        combined_df.drop_duplicates(subset="DT", keep="first", inplace=True)

        # Set 'DT' back as index
        combined_df.set_index("DT", inplace=True)

        # Sort the DataFrame by index
        combined_df_sorted = combined_df.sort_index()

        return combined_df_sorted


class NMDBinitializer:
    def __init__(
        self,
        config,
        start_date,
        end_date,
        station="JUNG",
        resolution="60",
        nmdb_table="revori",
    ):
        self.config = config
        self.start_date = start_date
        self.end_date = end_date
        self.station = station
        self.resolution = resolution
        self.nmdb_table = nmdb_table
        self.cache_dir = config.get_cache_dir()

    def create_cache_handler(self):
        return CacheHandler(self.cache_dir, self.station)

    def create_data_fetcher(self):
        return DataFetcher(
            self.start_date,
            self.end_date,
            self.station,
            self.resolution,
            self.nmdb_table,
        )

    def create_data_manager(self):
        return DataManager(
            self.start_date, self.end_date, self.cache_dir, self.station
        )


class NMDBDataHandler:
    def __init__(self, start_date, end_date, station="JUNG", initializer=None):
        """
        Initialize the NMDBDataHandler Class.

        Parameters
        ----------
        startdate : str
            The start date for data collection.
        enddate : str
            The end date for data collection.
        station : str, optional
            The station to collect data from, defaults to "JUNG".
        initializer : NMDBinitializer, optional
            An instance of NMDBinitializer to create necessary components.
        """
        # Use the provided initializer or create a new one
        self.initializer = (
            initializer
            if initializer
            else NMDBinitializer(
                cfg.COSMOSConfig, start_date, end_date, station
            )
        )
        self.start_date = start_date
        self.end_date = end_date
        self.station = station
        # Use the initializer to create necessary components
        self.cache_handler = self.initializer.create_cache_handler()
        self.data_fetcher = self.initializer.create_data_fetcher()
        self.data_manager = self.initializer.create_data_manager()
        self.has_cache = self.cache_handler.check_cache_file_exists()

    def collect_nmdb_data(self):
        """Wrapper function to collect nmdb data using the supplied info"""
        cache_file_path = os.path.join(
            self.initializer.cache_dir, f"nmdb_{self.station}.csv"
        )

        if self.has_cache:
            # Convert Timestamps to strings in 'YYYY-mm-dd' format if necessary
            if isinstance(self.start_date, pd.Timestamp):
                self.start_date = self.start_date.strftime("%Y-%m-%d")
            if isinstance(self.end_date, pd.Timestamp):
                self.end_date = self.end_date.strftime("%Y-%m-%d")
            self.data_manager.check_cache_range()
            self.data_manager.check_if_need_extra_data()

            try:
                # Read the cache
                df_cache = self.cache_handler.read_cache()
                if (
                    self.data_manager.need_data_before_cache
                    and self.data_manager.need_data_after_cache
                ):
                    df_download = self.data_fetcher.fetch_data_http()
                    df_combined = self.data_manager.append_and_sort_data(
                        df_cache, df_download
                    )
                    self.cache_handler.write_cache(df_combined)
                    return df_combined

                elif self.data_manager.need_data_before_cache:
                    # Only need to download data before the cached start date
                    self.data_fetcher.enddate = (
                        self.data_manager.cached_start_date
                    )
                    df_download = self.data_fetcher.fetch_data_http()
                    df_combined = self.data_manager.append_and_sort_data(
                        df_cache, df_download
                    )
                    self.cache_handler.write_cache(df_combined)
                    return df_combined

                elif self.data_manager.need_data_after_cache:
                    # Only need to download data after the cached end date
                    self.data_fetcher.startdate = (
                        self.data_manager.cached_end_date
                    )
                    df_download = self.data_fetcher.fetch_data_http()
                    df_combined = self.data_manager.append_and_sort_data(
                        df_cache, df_download
                    )
                    self.cache_handler.write_cache(df_combined)
                    return df_combined

                else:
                    # All data is in cache, no need to download
                    logging.info("All data is present in the cache.")
                    return df_cache

            except Exception as e:
                logging.error(f"Problem checking cache: {e}")
        else:
            logging.info(f"No cache file found at {cache_file_path}.")
            df_download = self.data_fetcher.fetch_data_http()
            self.cache_handler.write_cache(df_download)
            return df_download
