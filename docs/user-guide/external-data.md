We sometimes need to collect external data in order to fully process the CRNS. For example, in order to correct for incoming neturon intensity fluctuations, we need a reference data set. For this we have ways to directly interact wiht the [NMDB.eu](https://www.nmdb.eu) database. 

The NMDB.eu database collates high energy neutron monitor measurements in real-time from across the globe. An API is provided which neptoon can access directly within the overall pipeline. 

## Methods to download NMDB data

There are two main ways to download data from nmdb.eu. Using the standalone NMDB data downloader or by attaching data during the full CRNS processing pipeline

## Standalone NMDB data downloader

To create a dataframe of NMDB data you can use the `fetch_nmdb_data()` function as below:

```python
from neptoon.external import fetch_nmdb_data

df = fetch_nmdb_data(
    start_date="2022-01-01",
    end_date="2022-01-10",
    station="JUNG",
    resolution=60,
)
```

This will return a dataframe with the data from the selected station for the period shown. It will always download the data directly from NMDB.eu


## Collecting Neutrons in a python pipeline

At this stage we expect that you:

: - Have a CRNSDataHub with your time series data in it

### How to add NMDB data

```python
# if your data hub is called data_hub
data_hub.attach_nmdb_data(
    station = "JUNG",
    resolution = "60",
    nmdb_table = "revori",
    )
```

- **station:** neptoon supports the following stations: 

["JUNG", "SOPO", "OULU", "PSNM", "MXCO", "AATA", "INVK", "KIEL"]

- **resolution:** The resolution of the data in minutes
- **nmdb_table:** The specific table (recommended to use `revori` - revised original)

After running the above code, the crns data will have two additional columns, one with the NMDB monitor data, and one with a reference value for that particular monitor (taken as the average value over 30 years).

### What is happening?

When you run the above code in the data hub a few things happen. It finds the date range from the data you have in your hub. It creates an API call for the selected data over that particular date range and downloads it. It creates a cache of this data on your system. This prevents too many calls to the NMDB server when running many sites or testing things. In future calls it will first check to see if the date range and data are available already, if they are it uses this (offline) if more data is selected it will download this data and add it to the cache. 