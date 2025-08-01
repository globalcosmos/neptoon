import pandas as pd
import numpy as np
from saqc import SaQC
import datetime
from typing import List
from neptoon.data_audit import log_key_step
from neptoon.utils import (
    validate_timestamp_index,
    find_temporal_resolution_seconds,
    timedelta_to_freq_str,
    recalculate_neutron_uncertainty,
)
from neptoon.columns import ColumnInfo
from neptoon.logging import get_logger

core_logger = get_logger()

# TODO Clean up these into one module


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
        validate_timestamp_index(data_frame)
        self.data_frame = data_frame
        self.qc = SaQC(self.data_frame, scheme="simple")
        self.freq = self.return_frequency_str(self.data_frame)

    def return_frequency_str(self, data_frame):
        freq = find_temporal_resolution_seconds(data_frame=data_frame)
        freq = datetime.timedelta(seconds=freq)
        freq = timedelta_to_freq_str(freq)
        return freq

    @log_key_step("method", "freq")
    def align_timestamps(
        self,
        method: str = "time",
    ):
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
            freq=self.freq,
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


class TimeStampAggregator:
    """
    Uses routines from SaQC to aggregate the data to a new sample rate.
    When data is read in it is added to an SaQC object which is stored
    as an internal feature. Data can then be aggregated and converted
    back to a pd.DataFrame.

    """

    def __init__(
        self,
        data_frame: pd.DataFrame,
        output_resolution: str,
        max_na_fraction: float,
    ):
        """
        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame containing time series data.
        """
        validate_timestamp_index(data_frame)
        self.data_frame = data_frame
        self.qc = SaQC(self.data_frame, scheme="simple")
        self.output_resolution = self.ensure_output_res_is_str(
            output_resolution=output_resolution
        )
        self.avg_temporal_scaling_factor = (
            self._calc_avg_temporal_scaling_factor()
        )
        self.max_na_fraction = max_na_fraction
        self.max_na_int = self.convert_na_fraction_to_int(
            max_na_fraction=max_na_fraction
        )
        self.data_frame_is_aggregated = False

    def ensure_output_res_is_str(self, output_resolution):
        """
        Ensures that the output_resolution input is either a str
        representation (e.g., '1h') or a datetime.timedelta. If a
        datetime.timedelta it will convert it to string automatically.

        Parameters
        ----------
        output_resolution : str | datetime.timedelta
            The desired output temporal resolution

        Returns
        -------
        str
            Output resolution as str

        Raises
        ------
        ValueError
            If neither str or datetime.timedelta supplied
        """
        if isinstance(output_resolution, datetime.timedelta):
            return self.timedelta_to_freq_str(output_resolution)
        elif isinstance(output_resolution, str):
            return output_resolution
        else:
            raise ValueError(
                f"output_resolution must be str or datetime.timedelta"
                f", received: {type(output_resolution)}"
            )

    def _return_summable_col_list(self, columns: List | None = None):
        """
        Creates a list of the available columns that require summing
        aggregation.

        Parameters
        ----------
        columns : List, optional
            _description_, by default None
        """
        if columns is None:
            columns = [
                str(ColumnInfo.Name.EPI_NEUTRON_COUNT_RAW),
                str(ColumnInfo.Name.THERM_NEUTRON_COUNT_RAW),
                str(ColumnInfo.Name.PRECIPITATION),
            ]
        existing_columns = [
            col for col in self.data_frame.columns if col in columns
        ]
        return existing_columns

    def _calc_avg_temporal_scaling_factor(self):
        """
        Calculates the temporal scaling factor needed to convert input
        data to the desired output data resolution when data should be
        summed. E.g., precipitation data.

        It is also used in scaling the statistical uncertainty of
        neutrons in cph to account for the aggregation period.

        Returns
        -------
        _type_
            _description_
        """
        self.input_resolution = find_temporal_resolution_seconds(
            data_frame=self.data_frame
        )
        self.input_resolution = datetime.timedelta(
            seconds=self.input_resolution
        )
        temporal_scaling_factor = (
            pd.to_timedelta(self.output_resolution) / self.input_resolution
        )
        return round(temporal_scaling_factor)

    def convert_na_fraction_to_int(self, max_na_fraction: float):
        """
        Returns the maximum number of na values allowed in the
        aggregation window. Converted from a percentage into an absolute
        value

        Parameters
        ----------
        max_na_fraction : float
            Decimal fraction of max nan values in aggregation window

        Returns
        -------
        int
            max nan vals
        """
        return round(max_na_fraction * self.avg_temporal_scaling_factor)

    def _pre_align_dataframe(
        self,
        method="time",
    ):
        self.qc = self.qc.align(
            field=self.data_frame.columns,
            freq=timedelta_to_freq_str(self.input_resolution),
            method=method,
        )

    @log_key_step("method", "freq")
    def aggregate_data(
        self,
        method: str = "bagg",
    ):
        """
        Aggregates the data of the SaQC feature. Will automatically do
        this for all data columns. For more information on the values
        for method and freq see:

        https://rdm-software.pages.ufz.de/saqc/

        Parameters
        ----------
        method : str, optional
            Defaults to the nearest shift method to align time stamps.
            This means data is adjusted to the nearest time stamp
            without interpolation, by default "bagg".
        freq : str, optional
            The frequency of time stamps wanted, by default "1Hour"
        """
        self._pre_align_dataframe()
        # Columns for summing
        sum_column_list = self._return_summable_col_list()
        self.qc = self.qc.resample(
            field=sum_column_list,
            freq=self.output_resolution,
            method=method,
            func="sum",
            maxna=0,  # Must set to 0 as cannot sum with less than complete data
        )

        # Columns for mean
        remaining_column_list = [
            col for col in self.data_frame if col not in sum_column_list
        ]
        self.qc = self.qc.resample(
            field=remaining_column_list,
            freq=self.output_resolution,
            method=method,
            func="mean",
            maxna=self.max_na_int,
        )

        self.dataframe_aggregated = True
        self.data_frame = self.qc.data.to_pandas()
        if (
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)
            in self.data_frame.columns
        ):
            self.data_frame = recalculate_neutron_uncertainty(
                data_frame=self.data_frame,
                temporal_scaling_factor=self.avg_temporal_scaling_factor,
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
        return self.data_frame
