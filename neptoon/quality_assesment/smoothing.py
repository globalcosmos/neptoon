import pandas as pd
import numpy as np
from typing import Literal, Optional, Union

from neptoon.logging import get_logger

core_logger = get_logger()
""" 
Features:
    - Class for smoothing
    - neutrons and SM need "FINAL" ColumnInfo.Name variables
    - update feature to ensure code works on most current version of
      variable
    - method to ensure ColumnInfo is managed correctly
 """


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
        smooth_method: Literal[
            "rolling_mean", "savitsky_golay"
        ] = "rolling_mean",
        window: Optional[Union[str, int]] = 12,
        poly_order: Optional[int] = None,
    ):
        self.data = data
        self.smooth_method = smooth_method
        self.window = window
        self.poly_order = poly_order

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
            If incorrect method supplied
        ValueError
            If invalid time string supplied for rolling mean
        """
        if not isinstance(self.data.index, pd.DatetimeIndex):
            message = "Data index must be a DatetimeIndex"
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
        """_summary_

        Raises
        ------
        ValueError
            _description_
        ValueError
            _description_
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

    def _update_column_name_config(self):
        """
        This method will update the ConfigInfo.Name.... Final column
        """

    def apply_smoothing(self):

        return self.data.rolling(window=self.window, center=False)

    def _apply_rolling_mean(self):
        pass


temp_test_data = pd.DataFrame(
    np.random.randn(100),
    index=pd.date_range(start="2023-01-01", periods=100, freq="h"),
)

smoother = SmoothData(
    data=temp_test_data, smooth_method="rolling_mean", window=12
)
smoother.apply_smoothing()

## DOES NOT WORK - issue with data read in to fix
