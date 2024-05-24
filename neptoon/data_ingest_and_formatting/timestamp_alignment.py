from saqc import SaQC
import pandas as pd
from neptoon.data_management.data_audit import log_key_step

"""
We can use SaQC to align timestamps, this could be using same method for
all cols, or vary the method based on the value (e.g., interpolate for
SM, floor for Precipt etc.). We can use nshift (nearest shift) to begin
with?
"""


class TimeStampAligner:
    """
    Uses routines from SaQC to align the time stamps of the data to a
    common set. When data is read in it is added to an SaQC object which
    is stored as an internal feature. Data can then be aligned and
    converted back to a pd.DataFrame.
    """

    def __init__(self, data_frame: pd.DataFrame):
        """
        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame containing time series data.
        """
        self._validate_timestamp_index(data_frame)
        self.data_frame = data_frame
        self.qc = SaQC(self.data_frame, scheme="simple")

    def _validate_timestamp_index(self, data_frame):
        """
        Checks that the index of the dataframe is timestamp (essential
        for aligning the time stamps and using SaQC)

        Parameters
        ----------
        data_frame : pd.DataFrame
            The data frame imported into the TimeStampAligner

        Raises
        ------
        ValueError
            If the index is not datetime type
        """
        if not pd.api.types.is_datetime64_any_dtype(data_frame.index):
            raise ValueError("The DataFrame index must be of datetime type")

    def align_timestamps(self, method: str = "nshift", freq: str = "1Hour"):
        """
        Aligns the time stamp of the SaQC feature. Will automatically do
        this for all data columns. For more information on the values
        for method and freq see:

        https://rdm-software.pages.ufz.de/saqc/

        Parameters
        ----------
        method : str, optional
            Defaults to the nearest shift method to align time stamps.
            This means data is adjusted to the nearest time stamp
            without interpolation, by default "nshift".
        freq : str, optional
            The frequency of time stamps wanted, by default "1Hour"
        """

        self.qc = self.qc.align(field=data.columns, freq=freq, method=method)

    def return_dataframe(self):
        """
        Returns a pd.DataFrame from the SaQC object. Run this after
        alignment to return the aligned dataframe

        Returns
        -------
        df: pd.DataFrame
            DataFrame of time series data
        """
        df = self.qc.data.to_pandas()
        return df


# # Remove when ready
# data = pd.read_csv(
#     "https://git.ufz.de/rdm-software/saqc/raw/develop/docs/resources/data/data.csv",
#     index_col=0,
#     parse_dates=True,
# )

# tsa = TimeStampAligner(data)
# tsa.align_timestamps()
# tsa.return_dataframe()
