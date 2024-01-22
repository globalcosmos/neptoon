import os
import time
import re
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
            print(f"Error: '{date_str}' is not a recognizable date format.")
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

    def read_cache(self):
        """Read the cache file and return a DataFrame."""
        self.check_cache_file_exists()
        if self.cache_exists:
            filepath = os.path.join(self.cache_dir, f"nmdb_{self.station}.csv")
            try:
                return pd.read_csv(filepath)
            except FileNotFoundError:
                logging.error("Cache file not found.")
                return None
        else:
            print("Cache file does not exist")

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
        except FileNotFoundError:
            logging.error("Cache file not found when attempting to delete.")


class DataFetcher:
    def __init__(self, startdate, enddate, station="JUNG"):
        self.station = station
        self.startdate = startdate
        self.enddate = enddate

    def create_nmdb_url(self, method="http"):
        # Split dates for use in URL
        sy, sm, sd = str(
            DateTimeHandler.standardize_date(self.startdate)
        ).split("-")
        ey, em, ed = str(DateTimeHandler.standardize_date(self.enddate)).split(
            "-"
        )

        if method == "http":
            # Construct URL for data request
            url = (
                f"http://nest.nmdb.eu/draw_graph.php?wget=1"
                f"&stations[]={self.station}&tabchoice=1h&dtype=corr_for_efficiency"
                f"&tresolution=60&force=1&yunits=0&date_choice=bydate"
                f"&start_day={sd}&start_month={sm}&start_year={sy}"
                f"&start_hour=0&start_min=0&end_day={ed}&end_month={em}"
                f"&end_year={ey}&end_hour=23&end_min=59&output=ascii"
            )
        elif method == "html":
            # Construct URL for data request
            url = (
                f"http://nest.nmdb.eu/draw_graph.php?formchk=1"
                f"&stations[]={self.station}&tabchoice=1h&dtype=corr_for_efficiency"
                f"&tresolution=60&force=1&yunits=0&date_choice=bydate"
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

        except requests.exceptions.RequestException as e:
            print(f"HTTP Request failed: {e}")
            return None
        except ValueError as e:
            print(e)
            return None
        except pd.errors.ParserError as e:
            print(f"Error parsing data into DataFrame: {e}")
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
    def __init__(self, startdate, enddate, cache_dir, station):
        self.startdate = startdate
        self.enddate = enddate
        self.cache_dir = cache_dir
        self.station = station
        self.cache_handler = CacheHandler(cache_dir, station)
        self.data_fetcher = DataFetcher(startdate, enddate, station)
        self.has_cache = self.cache_handler.check_cache_file_exists()

    def check_cache_range(self):
        if self.cache_handler.cache_exists:
            df_cache = self.cache_handler.read_cache()
            df_cache["DT"] = pd.to_datetime(df_cache["DT"])
            # Get the date range in cache
            cached_start = df_cache["DT"].min()
            cached_end = df_cache["DT"].max()
            # Convert datetime objects to date for comparison
            self.cached_start_date = cached_start.date()
            self.cached_end_date = cached_end.date()

    def check_if_need_extra_data(self):
        start_date = pd.to_datetime(self.startdate).date()
        end_date = pd.to_datetime(self.enddate).date()

        need_data_before_cache = start_date < self.cached_start_date
        need_data_after_cache = end_date > self.cached_end_date

        return need_data_before_cache, need_data_after_cache

        #     df_download = self.get_data(startdate, enddate)
        #     dfnew = self.append_and_sort_data(df_cache, df_download)
        #     dfnew.to_csv(cache_file_path, index=False)  # Save new cache.
        # except Exception:  # Exception for when cache is not present
        #     df_download = self.get_data(startdate, enddate)
        #     df_download.to_csv(cache_file_path, index=False)

    def append_and_sort_data(self, df_cache, dfdownload):
        """Appends new data to cached data and sorts by date.

        Args:
            df_cache (DataFrame): The cached data.
            dfdownload (DataFrame): The newly downloaded data.

        Returns:
            DataFrame: The combined and sorted DataFrame.
        """
        # Concatenate the two DataFrames
        combined_df = pd.concat([df_cache, dfdownload])

        # Sort the DataFrame by the 'DATE' column
        combined_df_sorted = combined_df.sort_values(by="DATE")

        # Reset the index if necessary
        combined_df_sorted.reset_index(drop=True, inplace=True)

        return combined_df_sorted


class NMDBDataHandler:
    def __init__(self, station="JUNG", startdate="", enddate=""):
        """Initialize the NMDBDataFetcher Class

        Parameters
        ----------
        station : str, optional
            change station to another, by default "JUNG" testing a type
        startdate : str, optional
            _description_, by default ""
        enddate : str, optional
            _description_, by default ""
        """
        cfg.COSMOSConfig.check_and_create_cache()
        self.station = station
        self.startdate = startdate
        self.enddate = enddate
        self.cache_dir = cfg.COSMOSConfig.get_cache_dir()
        self.dfnmdb = None

    def fetch_and_append_data(self, startdate, enddate):
        """_summary_

        Args:
            startdate (_type_): _description_
            enddate (_type_): _description_
        """
        cache_file_path = os.path.join(
            self.cache_dir, f"nmdb_{self.station}.csv"
        )
        # Convert Timestamps to strings in 'YYYY-mm-dd' format if necessary
        if isinstance(startdate, pd.Timestamp):
            startdate = startdate.strftime("%Y-%m-%d")
        if isinstance(enddate, pd.Timestamp):
            enddate = enddate.strftime("%Y-%m-%d")

        try:
            df_cache = pd.read_csv(cache_file_path)
            df_cache["DATE"] = pd.to_datetime(df_cache["DATE"])
            df_download = self.get_data(startdate, enddate)
            dfnew = self.append_and_sort_data(df_cache, df_download)
            dfnew.to_csv(cache_file_path, index=False)  # Save new cache.
        except Exception:  # Exception for when cache is not present
            df_download = self.get_data(startdate, enddate)
            df_download.to_csv(cache_file_path, index=False)

    # @timed_function
    def collect_data(self):
        """Checks the cache and updates the start and end dates for data
        fetching if needed."""
        cache_file_path = os.path.join(
            self.cache_dir, f"nmdb_{self.station}.csv"
        )

        # if self.startdate or self.enddate are empty #

        if os.path.exists(cache_file_path):
            try:
                # Read the cache
                df_cache = pd.read_csv(cache_file_path)
                df_cache["DATE"] = pd.to_datetime(df_cache["DATE"])

                # Get the date range in cache
                cached_start = df_cache["DATE"].min()
                cached_end = df_cache["DATE"].max()
                # Convert datetime objects to date for comparison
                cached_start_date = cached_start.date()
                cached_end_date = cached_end.date()
                start_date = pd.to_datetime(self.startdate).date()
                end_date = pd.to_datetime(self.enddate).date()

                need_data_before_cache = start_date < cached_start_date
                need_data_after_cache = end_date > cached_end_date

                if need_data_before_cache and need_data_after_cache:
                    self.fetch_and_append_data(self.startdate, self.enddate)
                    df_cache = pd.read_csv(cache_file_path)
                    df_cache["DATE"] = pd.to_datetime(df_cache["DATE"])
                    print(1)
                    return df_cache

                elif need_data_before_cache:
                    # Only need to download data before the cached start date
                    self.fetch_and_append_data(self.startdate, cached_start)
                    df_cache = pd.read_csv(cache_file_path)
                    df_cache["DATE"] = pd.to_datetime(df_cache["DATE"])
                    print(2)
                    return df_cache

                elif need_data_after_cache:
                    # Only need to download data after the cached end date
                    self.fetch_and_append_data(cached_end, self.enddate)
                    df_cache = pd.read_csv(cache_file_path)
                    df_cache["DATE"] = pd.to_datetime(df_cache["DATE"])
                    print(3)
                    return df_cache

                else:
                    # All data is in cache, no need to download
                    print("All data is present in the cache.")
                    return df_cache

            except Exception as e:
                print(f"Problem checking cache: {e}")
        else:
            print(f"No cache file found at {cache_file_path}.")
            self.fetch_and_append_data(self.startdate, self.enddate)
            df_cache = pd.read_csv(cache_file_path)
            df_cache["DATE"] = pd.to_datetime(df_cache["DATE"])
            return df_cache
