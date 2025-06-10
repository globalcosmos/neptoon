import pandas as pd
from neptoon.columns.column_information import ColumnInfo
from neptoon.corrections.theory.air_humidity_corrections import (
    calc_absolute_humidity,
    calc_actual_vapour_pressure,
    calc_saturation_vapour_pressure,
)


class AbsoluteHumidityCreator:
    """
    Given a DataFrame with at least:
      - a temperature column (C)
      - a relative humidity column (in %)

    this class will add:
      1) saturation vapour pressure (hPa),
      2) actual vapour pressure,
      3) absolute humidity (g/m3).
    """

    def __init__(
        self,
        data_frame: pd.DataFrame,
        absolute_hum_col_name: str = str(ColumnInfo.Name.ABSOLUTE_HUMIDITY),
        temperature_col_name: str = str(ColumnInfo.Name.AIR_TEMPERATURE),
        sat_vapour_col_name: str = str(
            ColumnInfo.Name.SATURATION_VAPOUR_PRESSURE
        ),
        actual_vapour_pressure_col_name: str = str(
            ColumnInfo.Name.ACTUAL_VAPOUR_PRESSURE
        ),
        relative_hum_col_name: str = str(
            ColumnInfo.Name.AIR_RELATIVE_HUMIDITY
        ),
    ):
        self.data_frame = data_frame
        self.absolute_hum_col_name = absolute_hum_col_name
        self.temperature_col_name = temperature_col_name
        self.sat_vapour_col_name = sat_vapour_col_name
        self.actual_vapour_pressure_col_name = actual_vapour_pressure_col_name
        self.relative_hum_col_name = relative_hum_col_name

        # self._check_required_columns_available()

    def _check_required_columns_available(self):
        """
        Ensures that the required columns are available before processing.

        Raises
        ------
        KeyError
            Error when required column not available
        """
        missing = []
        for col in (self.temperature_col_name, self.relative_hum_col_name):
            if col not in self.data_frame.columns:
                missing.append(col)
        if missing:
            raise KeyError(
                f"DataFrame is missing required column(s): {missing}"
            )

    def check_if_abs_hum_exists(self):
        """
        Check if absolute humidity is already in the data frame

        Returns
        -------
        bool
        """
        if self.absolute_hum_col_name in self.data_frame.columns:
            abs_hum_exists = True
            return abs_hum_exists

    def create_saturation_vapour_pressure_data(self):
        """
        Creates a column with saturation vapour pressure, by applying
        calc_saturation_vapour_pressure to each temperature.
        """
        self.data_frame[self.sat_vapour_col_name] = self.data_frame[
            self.temperature_col_name
        ].apply(calc_saturation_vapour_pressure)

    def create_actual_vapour_pressure_data(self):
        """
        Creates a column with actual vapour pressure.
        """
        self.data_frame[self.actual_vapour_pressure_col_name] = (
            self.data_frame.apply(
                lambda row: calc_actual_vapour_pressure(
                    saturation_vapour_pressure=row[self.sat_vapour_col_name],
                    relative_humidity=row[self.relative_hum_col_name],
                ),
                axis=1,
            )
        )

    def create_absolute_humidity_data(self):
        """
        Creates a column with absolute humidity data.
        """
        self.data_frame[self.absolute_hum_col_name] = self.data_frame.apply(
            lambda row: calc_absolute_humidity(
                vapour_pressure=row[self.actual_vapour_pressure_col_name],
                temperature=row[self.temperature_col_name],
            ),
            axis=1,
        )

    def check_and_return_abs_hum_column(self):
        """
        Creates absolute humidity data whilst also creating saturation
        vapour pressure data and actual vapour pressure data.

        Returns the whole dataframe with new data attached.

        Returns
        -------
        pd.DataFrame
            DataFrame
        """
        abs_hum_exists = self.check_if_abs_hum_exists()  # returns if exists
        if abs_hum_exists:
            return self.data_frame
        else:
            self._check_required_columns_available()
            self.create_saturation_vapour_pressure_data()
            self.create_actual_vapour_pressure_data()
            self.create_absolute_humidity_data()
            return self.data_frame
