import pandas as pd
import numpy as np
from typing import Literal, Optional

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
        window: int = 12,
        poly_order: Optional[int] = None,
    ):
        self.data = data
        self.smooth_method = smooth_method
        self.window = window
        self.poly_order = poly_order

        self._validate_inputs()

    def _validate_inputs(self):
        if self.smooth_method not in ["rolling_mean", "savitsky_golay"]:
            message = (
                "smooth_method must be either 'rolling_mean' or "
                "'savitsky_golay'"
            )
            core_logger.error(message)
            raise ValueError(message)
        if self.smooth_method == "rolling_mean":
            self._validate_rolling_mean_params()
        elif self.smooth_method == "savitsky_golay":
            self._validate_savitsky_golay_params()

    def _validate_savitsky_golay_params(self):
        if self.poly_order is None:
            message = (
                "poly_order cannot be None when implementing SG filter. "
                "Either change the smoothing method or supply a poly_order value"
            )
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
        # read data
        # smooth data
        # return data
        pass

    def _apply_rolling_mean():
        pass


temp_test_data = pd.Series(
    np.random.randn(100),
    index=pd.date_range(start="2023-01-01", periods=100, freq="h"),
)

smoother = SmoothData(data=temp_test_data)
smoother.data
