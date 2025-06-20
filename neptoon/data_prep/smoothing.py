import pandas as pd
from typing import Literal, Optional, Union
from scipy.signal import savgol_filter

from neptoon.logging import get_logger
from neptoon.columns import ColumnInfo
from neptoon.utils import parse_resolution_to_timedelta

core_logger = get_logger()


class SmoothData:
    """
    A class for smoothing data using a variety of different methods.

    This class provides functionality to smooth time series data using
    different methods such as rolling mean and Savitzky-Golay filter. It
    supports both count-based and time-based windows for the rolling
    mean method.

    """

    def __init__(
        self,
        data: pd.Series,
        column_to_smooth: str,
        smooth_method: Literal[
            "rolling_mean", "savitsky_golay"
        ] = "rolling_mean",
        window: str = "12h",
        min_proportion_good_data: float = 0.5,
        poly_order: Optional[int] = None,
        auto_update_final_col: bool = True,
    ):
        """
        Attributes for SmoothData

        Parameters
        ----------
        data : pd.Series
            Data to be smoothed - must be time indexed
        column_to_smooth : str
            The column name of the column to be smoothed.
        smooth_method : Literal["rolling_mean", "savitsky_golay"],
            The smooth method to apply, by default "rolling_mean"
        window : str , optional
            The window size for smoothing. Time based str value e.g.,
            30m, 1h, 6h, 1d by default 24h. Converted to timedelta for
            use in smoothing.
        min_proportion_good_data : float, optional
            The minimum proportion of available data in the window for a
            average to be taken, provided as a decimal.
        poly_order : Optional[int], optional
            Poly order to apply (savitsky golay only), by default None
        auto_update_final_col : bool, optional
            Whether to update the ColumnInfo object to represent the new
            column as _FINAL, by default True
        """
        self.data = data
        self.column_to_smooth = column_to_smooth
        self.smooth_method = smooth_method
        self.window = window
        self.min_proportion_good_data = min_proportion_good_data
        self.poly_order = poly_order
        self.auto_update_final_col = auto_update_final_col

        # Placeholders
        self.window_as_timedelta = None

        self._validate_inputs()

    def _validate_inputs(self):
        """
        Validate the inputs in SmoothData class to ensure selected
        smoothing method can be applied with given data.

        Raises
        ------
        ValueError
            If not DateTmeIndex in data
        ValueError
            If unsupported method is supplied
        ValueError
            If invalid time string supplied for rolling mean
        """
        if not isinstance(self.data.index, pd.DatetimeIndex):
            message = "Data index must be a DatetimeIndex"
            core_logger.error(message)
            raise ValueError(message)
        if not isinstance(self.column_to_smooth, str):
            message = "column_to_smooth must be a string type"
            core_logger.error(message)
            raise ValueError(message)
        if self.smooth_method not in ["rolling_mean", "savitsky_golay"]:
            message = (
                "smooth_method must be either 'rolling_mean' or "
                "'savitsky_golay'"
            )
            core_logger.error(message)
            raise ValueError(message)
        if self.smooth_method == "savitsky_golay":
            self._switch_to_rolling()  # TODO : change this when implementing savitsky_golay
            # self._validate_savitsky_golay_params()
        if self.smooth_method == "rolling_mean":
            self._validate_rolling_mean_params()
        if isinstance(self.window, str):
            self.window_as_timedelta = parse_resolution_to_timedelta(
                resolution_str=self.window
            )
        else:
            message = (
                f"Invalid time string for window: {self.window}"
                "`window` must be a string type denoting the time window for "
                "smoothing. E.g., 30 minutes = `30m`, 2 hours = `2h`, 1 day = `1d`"
            )
            core_logger.error(message)
            raise ValueError(message)

    def _validate_rolling_mean_params(self):
        if not isinstance(self.window, str):
            message = (
                "window must be given as a string (e.g., 1h, 1d, 30m). "
                f"Window was given as {self.window}"
            )
            core_logger.error(message)
            raise ValueError(message)

    def _switch_to_rolling(self):
        self.smooth_method = "rolling_mean"
        message = (
            "Savitsky-Golay smoothing is coming in a future update."
            "For this processing pipeline smoothing has been changed to rolling mean."
        )
        core_logger.info(message)
        print(message)

    def _validate_savitsky_golay_params(self):
        """
        Validates that the parameters are appropriate for using savitsky
        golay smoothing.

        Raises
        ------
        ValueError
            error if polyorder not supplied
        ValueError
            error if time based window given
        """
        if self.poly_order is None:
            message = (
                "poly_order cannot be None when implementing SG filter. "
                "Either change the smoothing method or supply a poly_order value"
            )
            core_logger.error(message)
            raise ValueError(message)
        if isinstance(self.window, str):
            message = "Time-based window is not supported for Savitzky-Golay smoothing"
            core_logger.error(message)
            raise ValueError(message)

    def _update_column_name_config(
        self,
        possible_names=[
            str(ColumnInfo.Name.SOIL_MOISTURE_VOL),
            str(ColumnInfo.Name.SOIL_MOISTURE_VOL_FINAL),
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL),
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT),
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL),
        ],
    ):
        """
        Updates the value for the '_FINAL' value in ColumnInfo.
        Currently restricted to EPI_NEUTRONS and SOIL_MOISTURE. These
        are most likely to be smoothed and used throughout the code.

        The possible_names parameter is included to give flexibility in
        future with updating the names. (i.e., we could include support
        for supplying other columns to be automatically updated with
        '_FINAL' after smoothing)

        Parameters
        ----------
        possible_names : list, optional
            _description_, by default [
            str(ColumnInfo.Name.SOIL_MOISTURE),
            str(ColumnInfo.Name.SOIL_MOISTURE_FINAL),
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL),
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT),
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL), ]
        """
        if not self.auto_update_final_col:
            return
        if self.column_to_smooth not in possible_names:
            message = (
                f"{self.column_to_smooth} is not supported for automatic "
                "updating of ColumnInfo. Please turn off auto_update_final_col"
            )
            core_logger.error(message)
            raise ValueError(message)

        new_column_name = self.create_new_column_name()
        if self.column_to_smooth in [
            str(ColumnInfo.Name.SOIL_MOISTURE_VOL),
            str(ColumnInfo.Name.SOIL_MOISTURE_VOL_FINAL),
        ]:
            ColumnInfo.relabel(
                ColumnInfo.Name.SOIL_MOISTURE_VOL_FINAL,
                new_label=new_column_name,
            )
        elif self.column_to_smooth in [
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL),
        ]:
            ColumnInfo.relabel(
                ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL,
                new_label=new_column_name,
            )
        elif self.column_to_smooth in [
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT),
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL),
        ]:
            ColumnInfo.relabel(
                ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL,
                new_label=new_column_name,
            )

    def _get_min_obs_for_rolling_mean(
        self,
        data_to_smooth: pd.Series,
        min_proportion_good_data: float = 0.5,
    ):
        """
        Calculates the number of observations that equates to half the
        timedelta window.

        Necessary as pd.Series.rolling(min_periods) only accepts
        integers (not timedelta)

        Parameters
        ----------
        data_to_smooth : pd.Series
            data on which smoothing will be done (datetime index)

        Returns
        -------
        int
            The number of observatinos that make up the half the time
            delta
        """
        freq = data_to_smooth.index.to_series().diff().median()
        min_obs = int(
            (self.window_as_timedelta * min_proportion_good_data) / freq
        )
        return min_obs

    def _apply_rolling_mean(self, data_to_smooth: pd.Series):
        """
        Applies a rolling mean smoothing

        Parameters
        ----------
        data_to_smooth : pd.Series
            pd.Series of data to smooth

        Returns
        -------
        pd.Series
            The smoothed data
        """
        min_obs = self._get_min_obs_for_rolling_mean(
            data_to_smooth=data_to_smooth
        )

        smoothed = data_to_smooth.rolling(
            window=self.window_as_timedelta,
            min_periods=min_obs,
            center=False,
        ).mean()

        return smoothed.round()

    def _apply_savitsky_golay(self, data_to_smooth):
        """
        Applies the savitsky golay smoothing technique

        Parameters
        ----------
        data_to_smooth : str
            column name to be smoothed

        Returns
        -------
        pd.Series
            smoothed series

        #TODO
        THIS DOESN'T WORK WHEN NAN VALUES ARE IN WINDOW.

        """

        smoothed = savgol_filter(
            x=data_to_smooth,
            window_length=self.window,
            polyorder=self.poly_order,
        )
        return pd.Series(smoothed, index=self.data.index).round()

    def create_new_column_name(self):
        """
        Creates a new column name based on the supplied column_to_smooth
        name. This depends on method and parameters used.

        Returns
        -------
        str
            New column name
        """
        og_column_name = self.column_to_smooth + "_"

        if self.smooth_method == "rolling_mean":
            add_on = f"rollingmean_{str(self.window)}"
        elif self.smooth_method == "savitsky_golay":
            add_on = f"savgol_{str(self.window)}_{str(self.poly_order)}"

        return og_column_name + add_on

    def apply_smoothing(self):
        """
        Function to apply smoothing to a Series of data. It is presumed
        that the appropriate attributes have been assigned already.

        Returns
        -------
        pd.Series
            The smoothed Series
        """
        if self.smooth_method == "rolling_mean":
            self._update_column_name_config()
            return self._apply_rolling_mean(self.data)
        elif self.smooth_method == "savitsky_golay":
            self._update_column_name_config()
            return self._apply_savitsky_golay(self.data)
