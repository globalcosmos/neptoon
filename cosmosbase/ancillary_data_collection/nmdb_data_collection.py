import pandas as pd
from bs4 import BeautifulSoup
import urllib
from dateutil import parser
import cosmosbase.configuration.config as cfg ### !!!
import os

class NMDBDataHandler:
    def __init__(self, 
                 station='JUNG', 
                 defaultdir='', 
                 startdate='', 
                 enddate=''):
        """Initialize the NMDBDataFetcher Class

        Args:
            station (str, optional): if using different station provide the string here. Defaults to 'JUNG'.
            defaultdir (str, optional): Default working directory. Defaults to ''.
            startdate (str, optional): First date from which data is required.
            enddate (str, optional): Last date from which data is required.
        """
        self.station = station
        self.defaultdir = defaultdir
        self.startdate = self.standardize_date(startdate)
        self.enddate = self.standardize_date(enddate)
        self.cache_dir = cfg.AppConfig.get_cache_dir()
    
    @staticmethod
    def standardize_date(date_str):
        """Checks the provided date format and converts to necessary format.

        Args:
            date_str (any): String representing the date

        Returns:
            formatted date: Returns the formatted date in the format YYYY-mm-dd
        """
        try:
            # Parse the date
            parsed_date = parser.parse(date_str)
            # Convert to standard format (e.g., YYYY-mm-dd)
            standardized_date_str = parsed_date.strftime('%Y-%m-%d')
            return standardized_date_str

        except ValueError:
            # Handle the error if the date format is unrecognized
            print(f"Error: '{date_str}' is not a recognizable date format.")
            return None
        
    def delete_cache_file(self):
        confirmation = input("Are you sure you want to delete the cached NMDB data? (yes/no): ")
        if confirmation.lower() in ['no', 'n']:
            print('Aborted.')
            pass
        elif confirmation.lower() in ['yes', 'y']:
            directory = self.cache_dir
            filename = f'nmdb_{self.station}.csv'
            os.remove(os.path.join(directory, filename))
            print('Cache file deleted')
        else:
            print("Please type yes if you wish to delete the cache. Aborted.")

    def check_cache(self):
        directory = self.cache_dir
        filename = f'nmdb_{self.station}.csv'
        file_path = os.path.join(directory, filename)
        try:
            df = pd.read_csv(file_path)
            df['DATE'] = pd.to_datetime(df['DATE'])
            mindate = df['DATE'].min()
            maxdate = df['DATE'].max()
            
            # if mindate <= self.startdate and maxdate <=:
            #     self.startdate = maxdate
            # if self.startdate 
            
        except Exception as e:
            print(f'Problem checking cache: {e}')

    def get_data(self):
        """nmdb_get will collect data for Junfraujoch station that is required to calculate fsol.
        Returns a dictionary that can be used to fill in values to the main dataframe
        of each site.

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
        sy, sm, sd = str(self.startdate).split("-")
        ey, em, ed = str(self.enddate).split("-")

        # Construct URL for data request
        url = f"http://nest.nmdb.eu/draw_graph.php?formchk=1&stations[]={self.station}&tabchoice=1h&dtype=corr_for_efficiency&tresolution=60&force=1&yunits=0&date_choice=bydate&start_day={sd}&start_month={sm}&start_year={sy}&start_hour=0&start_min=0&end_day={ed}&end_month={em}&end_year={ey}&end_hour=23&end_min=59&output=ascii"
        
        # Fetch and read the HTML content
        response = urllib.request.urlopen(url)
        html = response.read()
        
        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html, features="html.parser")
        pre = soup.find('pre').text

        # Extract and process data from the <pre> tag
        data = pre[pre.find('start_date_time'):].replace("start_date_time   1HCOR_E", "")
        lines = data.strip().split('\n')[1:]  # Skip header line

        # Create DataFrame from the processed lines
        dfneut = pd.DataFrame([line.split(';') for line in lines], columns=['DATE', 'COUNT'])
        dfneut['DATE'] = pd.to_datetime(dfneut['DATE'])
        dfneut['COUNT'] = dfneut['COUNT'].astype(float)
        
        self.nmdbdata = dfneut

    def append_cache():
        pass