import pandas as pd
from saqc import SaQC

from neptoon.data_audit import log_key_step


class TimeStampAligner:
    """
    Uses routines from SaQC to align the time stamps of the data to a
    common set. When data is read in it is added to an SaQC object which
    is stored as an internal feature. Data can then be aligned and
    converted back to a pd.DataFrame.

    Example
    -------
    >>> import pandas as pd
    >>> from neptoon.data_ingest_and_formatting.timestamp_alignment import (
    ...    TimeStampAligner
    ... )
    >>> data = {'value': [1, 2, 3, 4]}
    >>> index = pd.to_datetime(
    ...     [
    ...         "2021-01-01 00:04:00",
    ...         "2021-01-01 01:10:00",
    ...         "2021-01-01 02:05:00",
    ...         "2021-01-01 02:58:00",
    ...     ]
    ... )
    >>> df = pd.DataFrame(data, index=index)
    >>> # Initialize the TimeStampAligner
    >>> time_stamp_aligner = TimeStampAligner(df)
    >>> # Align timestamps
    >>> time_stamp_aligner.align_timestamps(method='nshift', freq='1H')
    >>> # Get the aligned dataframe
    >>> aligned_df = time_stamp_aligner.return_dataframe()
    >>> print(aligned_df)
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

    @log_key_step("method", "freq")
    def align_timestamps(self, freq: str = "1h", method: str = "time"):
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
            without interpolation, by default "time".
        freq : str, optional
            The frequency of time stamps wanted, by default "1Hour"
        """

        self.qc = self.qc.align(
            field=self.data_frame.columns,
            freq=freq,
            method=method,
        )

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
