import pandas as pd
from bs4 import BeautifulSoup
import urllib
from dateutil import parser
import cosmosbase.configuration.config as cfg
import os
import time


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


class NMDBDataHandler:
    def __init__(
        self, station="JUNG", defaultdir="", startdate="", enddate=""
    ):
        """Initialize the NMDBDataFetcher Class

        Parameters
        ----------
        station : str, optional
            change station to another, by default "JUNG" testing a type
        defaultdir : str, optional
            Default working directory, by default "" testing an extra
            long sentence using the tool
        startdate : str, optional
            _description_, by default ""
        enddate : str, optional
            _description_, by default ""
        """
        cfg.COSMOSConfig.check_and_create_cache()
        self.station = station
        self.defaultdir = defaultdir
        self.startdate = self.standardize_date(startdate)
        self.enddate = self.standardize_date(enddate)
        self.cache_dir = cfg.COSMOSConfig.get_cache_dir()
        self.dfnmdb = None

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

    def delete_cache_file(self):
        """Delete the cached file for the current instance."""
        directory = self.cache_dir
        filename = f"nmdb_{self.station}.csv"
        os.remove(os.path.join(directory, filename))
        print("Cache file deleted")

    def get_data(self, startdate, enddate):
        """Will collect data from defined station.
        Returns a dictionary of values

        Parameters
        ----------
        startdate : datetime
            start date of desire data in format YYYY-mm-dd
                e.g 2015-10-01
        enddate : datetime
            end date of desired data in format YYYY-mm-dd

        Returns
        -------
        df
            df of neutron count data from NMDB.eu
        """
        # Split dates for use in URL
        sy, sm, sd = str(self.standardize_date(startdate)).split("-")
        ey, em, ed = str(self.standardize_date(enddate)).split("-")

        # Construct URL for data request
        url = (
            f"http://nest.nmdb.eu/draw_graph.php?formchk=1"
            f"&stations[]={self.station}&tabchoice=1h&dtype=corr_for_efficiency"
            f"&tresolution=60&force=1&yunits=0&date_choice=bydate"
            f"&start_day={sd}&start_month={sm}&start_year={sy}"
            f"&start_hour=0&start_min=0&end_day={ed}&end_month={em}"
            f"&end_year={ey}&end_hour=23&end_min=59&output=ascii"
        )

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
            [line.split(";") for line in lines], columns=["DATE", "COUNT"]
        )
        dfneut["DATE"] = pd.to_datetime(dfneut["DATE"])
        dfneut["COUNT"] = dfneut["COUNT"].astype(float)

        return dfneut

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

    @timed_function
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
