import pandas as pd
from typing import Literal, Optional, Union
from scipy.signal import savgol_filter

from neptoon.logging.logging import get_logger
from neptoon.column_names.column_information import ColumnInfo

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
        window: Optional[Union[str, int]] = 12,
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
        window : Optional[Union[str, int]], optional
            The window size for smoothing, by default 12
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
        self.poly_order = poly_order
        self.auto_update_final_col = auto_update_final_col

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
            self._validate_savitsky_golay_params()
        if self.smooth_method == "rolling_mean":
            self._validate_rolling_mean_params()
        if isinstance(self.window, str):
            try:
                pd.Timedelta(self.window)
            except ValueError:
                message = f"Invalid time string for window: {self.window}"
                core_logger.error(message)
                raise ValueError(message)

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

    def _validate_rolling_mean_params(self):
        "TODO: could implement time delta selection here?"
        pass

    def _update_column_name_config(
        self,
        possible_names=[
            str(ColumnInfo.Name.SOIL_MOISTURE),
            str(ColumnInfo.Name.SOIL_MOISTURE_FINAL),
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL),
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
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL), ]
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
            str(ColumnInfo.Name.SOIL_MOISTURE),
            str(ColumnInfo.Name.SOIL_MOISTURE_FINAL),
        ]:
            ColumnInfo.relabel(
                ColumnInfo.Name.SOIL_MOISTURE_FINAL, new_label=new_column_name
            )
        elif self.column_to_smooth in [
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_CPH),
            str(ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL),
        ]:
            ColumnInfo.relabel(
                ColumnInfo.Name.EPI_NEUTRON_COUNT_FINAL,
                new_label=new_column_name,
            )

    def _apply_rolling_mean(self, data_to_smooth):
        """
        Applies a rolling mean smoothing

        Parameters
        ----------
        data_to_smooth : str
            The name of the column to smooth

        Returns
        -------
        pd.Series
            The smoothed data
        """
        if isinstance(self.window, int):
            return data_to_smooth.rolling(
                window=self.window,
                min_periods=int((self.window / 2)),
                center=False,
            ).mean()
        else:
            # TODO: Need to address min periods using TimeDelta
            return data_to_smooth.rolling(
                window=self.window,
                min_periods=2,
                center=False,
            ).mean()

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
        """
        smoothed = savgol_filter(
            x=data_to_smooth,
            window_length=self.window,
            polyorder=self.poly_order,
        )
        return pd.Series(smoothed, index=self.data.index)

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
