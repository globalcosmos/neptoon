import pandas as pd
import numpy as np
import copy
from datetime import timedelta
from typing import Literal, List
from dataclasses import dataclass, field
import statistics

# from scipy.optimize import minimize
from neptoon.columns import ColumnInfo
from neptoon.corrections import (
    Schroen2017,
    neutrons_to_total_grav_soil_moisture_desilets_etal_2010,
    neutrons_to_total_grav_soil_moisture_koehli_etal_2021,
)

from neptoon.data_prep.conversions import AbsoluteHumidityCreator


def _create_water_equiv_soc(soil_organic_carbon: float):
    return soil_organic_carbon * 0.555


class CalibrationConfiguration:
    """
    User facing configuration class for calibration steps. Here a user
    can add information required for calibration. Defaults can often
    also be used if following similar data structure and naming as
    neptoon uses as standard.
    """

    def __init__(
        self,
        # Settings
        hours_of_data_around_calib: int = 6,
        converge_accuracy: float = 0.01,
        neutron_conversion_method: Literal[
            "desilets_etal_2010", "koehli_etal_2021"
        ] = "desilets_etal_2010",
        koehli_parameters: Literal[
            "Jan23_uranos",
            "Jan23_mcnpfull",
            "Mar12_atmprof",
            "Mar21_mcnp_drf",
            "Mar21_mcnp_ewin",
            "Mar21_uranos_drf",
            "Mar21_uranos_ewin",
            "Mar22_mcnp_drf_Jan",
            "Mar22_mcnp_ewin_gd",
            "Mar22_uranos_drf_gd",
            "Mar22_uranos_ewin_chi2",
            "Mar22_uranos_drf_h200m",
            "Aug08_mcnp_drf",
            "Aug08_mcnp_ewin",
            "Aug12_uranos_drf",
            "Aug12_uranos_ewin",
            "Aug13_uranos_atmprof",
            "Aug13_uranos_atmprof2",
        ] = "Mar21_mcnp_drf",
        horizontal_weight_method: Literal[
            "schroen_etal_2017", "equal"
        ] = "schroen_etal_2017",
        vertical_weight_method: Literal[
            "schroen_etal_2017", "equal"
        ] = "schroen_etal_2017",
        # Calibration Data Settings
        calib_data_date_time_column_name: str | None = None,
        calib_data_date_time_format: str = "%Y-%m-%d %H:%M",
        sample_depth_column: str | None = None,
        distance_column: str | None = None,
        bulk_density_of_sample_column: str | None = None,
        profile_id_column: str | None = None,
        soil_moisture_gravimetric_column: str | None = None,
        soil_organic_carbon_column: str | None = None,
        lattice_water_column: str | None = None,
        # Time Series Data Settings
        temperature_column: str | None = None,
        relative_humidity_column: str | None = None,
        abs_air_humidity_column: str | None = None,
        neutron_column_name: str | None = None,
        air_pressure_column_name: str | None = None,
        value_avg_lattice_water: float | None = None,
        value_avg_bulk_density: float | None = None,
        value_avg_soil_organic_carbon: float | None = None,
    ):
        """
        User-facing configuration for calibration parameters.

        Parameters
        ----------
        hours_of_data_around_calib : int, optional
            Number of hours of neutron count data to include around the
            datetime stamp for calibration. This window is used to
            gather measurements from sensors during the calibration
            period. Default is 6.
        converge_accuracy : float, optional
            The convergence threshold for when finding n0. Default is
            0.01.
        neutron_conversion_method : {"desilets_etal_2010",
        "koehli_etal_2021"}, optional
            The conversion method used to translate raw neutron counts
            into soil moisture estimates. Options are
            "desilets_etal_2010" or "koehli_etal_2021". Default is
            "desilets_etal_2010".
        koehli_parameters : str, optional
            Parameter set to use when koehli_etal_2021 method is
            selected. Default is "Mar21_uranos_drf".
        horizontal_weight_method : {"schroen_etal_2017", "equal"},
        optional
            Method for horizontal weighting. Default is
            "schroen_etal_2017".
        vertical_weight_method : {"schroen_etal_2017", "equal"},
        optional
            Method for vertical weighting. Default is
            "schroen_etal_2017".
        calib_data_date_time_column_name : str, optional
            The name of the column containing date‐time information for
            each calibration day. If None, uses default from ColumnInfo.
        calib_data_date_time_format : str, optional
            Format string for parsing date-time values. Default is
            "%Y-%m-%d %H:%M".
        sample_depth_column : str, optional
            The name of the column with sample depth values (cm). If
            None, uses default from ColumnInfo.
        distance_column : str, optional
            The name of the column stating the distance of the sample
            from the sensor (meters). If None, uses default from
            ColumnInfo.
        bulk_density_of_sample_column : str, optional
            The name of the column with bulk density values of the
            samples (g/cm^3). If None, uses default from ColumnInfo.
        profile_id_column : str, optional
            Name of the column with profile IDs. If None, uses default
            from ColumnInfo.
        soil_moisture_gravimetric_column : str, optional
            Name of the column with gravimetric soil moisture values
            (g/g). If None, uses default from ColumnInfo.
        soil_organic_carbon_column : str, optional
            Name of the column with soil organic carbon values (g/g). If
            None, uses default from ColumnInfo.
        lattice_water_column : str, optional
            Name of the column with lattice water values (g/g). If None,
            uses default from ColumnInfo.
        temperature_column : str, optional
            Name of the column with temperature values. If None, uses
            default from ColumnInfo.
        relative_humidity_column : str, optional
            Name of the column with relative humidity values. If None,
            uses default from ColumnInfo.
        abs_air_humidity_column : str, optional
            Name of the column with absolute air humidity values
            (g/cm3). If None, uses default from ColumnInfo.
        neutron_column_name : str, optional
            Name of the column with corrected neutrons in it. If None,
            uses default from ColumnInfo.
        air_pressure_column_name : str, optional
            Name of the column with air pressure values in it. If None,
            uses default from ColumnInfo.
        value_avg_lattice_water: float, optional
            The actual site average lattice water value. Default is 0.
        value_avg_bulk_density: float, optional
            The actual site average dry soil bulk density. Default is 0.
        value_avg_soil_organic_carbon: float, optional
            The actual site average soil organic carbon. Default is 0.
        """
        # Processing settings
        self.hours_of_data_around_calib = hours_of_data_around_calib
        self.converge_accuracy = converge_accuracy
        self.neutron_conversion_method = neutron_conversion_method
        self.koehli_parameters = koehli_parameters
        self.horizontal_weight_method = horizontal_weight_method
        self.vertical_weight_method = vertical_weight_method

        # Date/time settings
        self.calib_data_date_time_column_name = (
            calib_data_date_time_column_name
        )
        self.calib_data_date_time_format = calib_data_date_time_format

        # Column names (user can override defaults by providing values)
        self.sample_depth_column = sample_depth_column
        self.distance_column = distance_column
        self.bulk_density_of_sample_column = bulk_density_of_sample_column
        self.profile_id_column = profile_id_column
        self.soil_moisture_gravimetric_column = (
            soil_moisture_gravimetric_column
        )
        self.soil_organic_carbon_column = soil_organic_carbon_column
        self.lattice_water_column = lattice_water_column
        self.temperature_column = temperature_column
        self.relative_humidity_column = relative_humidity_column
        self.abs_air_humidity_column = abs_air_humidity_column
        self.neutron_column_name = neutron_column_name
        self.air_pressure_column_name = air_pressure_column_name

        # Extra
        # Site average values
        self.value_avg_lattice_water = value_avg_lattice_water
        self.value_avg_bulk_density = value_avg_bulk_density
        self.value_avg_soil_organic_carbon = value_avg_soil_organic_carbon


@dataclass
class CalibrationContext:
    """
    Internal context for data processing - outputs of each stage are
    written here. Contains resolved column names and processed values.
    """

    # Configuration Values @
    # Processing settings
    hours_of_data_around_calib: int | None = None
    converge_accuracy: float | None = None
    neutron_conversion_method: str | None = None
    koehli_parameters: str | None = None
    horizontal_weight_method: str | None = None
    vertical_weight_method: str | None = None

    # Date/time settings
    calib_data_date_time_column_name: str | None = None
    calib_data_date_time_format: str | None = None

    # Resolved column names
    sample_depth_column: str | None = None
    distance_column: str | None = None
    bulk_density_of_sample_column: str | None = None
    profile_id_column: str | None = None
    soil_moisture_gravimetric_column: str | None = None
    soil_organic_carbon_column: str | None = None
    lattice_water_column: str | None = None
    temperature_column: str | None = None
    relative_humidity_column: str | None = None
    abs_air_humidity_column: str | None = None
    neutron_column_name: str | None = None
    air_pressure_column_name: str | None = None

    # Site average values
    value_avg_lattice_water: float | None = None
    value_avg_bulk_density: float | None = None
    value_avg_soil_organic_carbon: float | None = None
    value_avg_soil_organic_carbon_water_equiv: float | None = None

    # Derived values #
    unique_calibration_days: list = field(default_factory=list)
    list_of_data_frames: list = field(default_factory=list)
    list_of_profiles: list = field(default_factory=list)
    calib_day_df_dict: dict = field(default_factory=dict)
    calib_metrics_dict: dict = field(default_factory=dict)
    calibration_results_by_day: dict = field(default_factory=dict)
    weights_df: pd.DataFrame = field(default_factory=pd.DataFrame)

    @classmethod
    def from_config(cls, config: CalibrationConfiguration):
        """
        Convert configuration to context, resolving all None values to defaults
        from ColumnInfo and calculating derived values.

        Parameters
        ----------
        config : CalibrationConfiguration
            User configuration object

        Returns
        -------
        CalibrationContext
            Internal processing context with all values resolved
        """
        # Resolve column names - use config value if provided, otherwise default
        calib_data_date_time_column_name = (
            config.calib_data_date_time_column_name
            if config.calib_data_date_time_column_name is not None
            else str(ColumnInfo.Name.DATE_TIME)
        )

        sample_depth_column = (
            config.sample_depth_column
            if config.sample_depth_column is not None
            else str(ColumnInfo.Name.CALIB_DEPTH_OF_SAMPLE)
        )

        distance_column = (
            config.distance_column
            if config.distance_column is not None
            else str(ColumnInfo.Name.CALIB_DISTANCE_TO_SENSOR)
        )

        bulk_density_of_sample_column = (
            config.bulk_density_of_sample_column
            if config.bulk_density_of_sample_column is not None
            else str(ColumnInfo.Name.CALIB_BULK_DENSITY)
        )

        profile_id_column = (
            config.profile_id_column
            if config.profile_id_column is not None
            else str(ColumnInfo.Name.CALIB_PROFILE_ID)
        )

        soil_moisture_gravimetric_column = (
            config.soil_moisture_gravimetric_column
            if config.soil_moisture_gravimetric_column is not None
            else str(ColumnInfo.Name.CALIB_SOIL_MOISTURE_GRAVIMETRIC)
        )

        soil_organic_carbon_column = (
            config.soil_organic_carbon_column
            if config.soil_organic_carbon_column is not None
            else str(ColumnInfo.Name.CALIB_SOIL_ORGANIC_CARBON)
        )

        lattice_water_column = (
            config.lattice_water_column
            if config.lattice_water_column is not None
            else str(ColumnInfo.Name.CALIB_LATTICE_WATER)
        )

        temperature_column = (
            config.temperature_column
            if config.temperature_column is not None
            else str(ColumnInfo.Name.AIR_TEMPERATURE)
        )

        relative_humidity_column = (
            config.relative_humidity_column
            if config.relative_humidity_column is not None
            else str(ColumnInfo.Name.AIR_RELATIVE_HUMIDITY)
        )

        abs_air_humidity_column = (
            config.abs_air_humidity_column
            if config.abs_air_humidity_column is not None
            else str(ColumnInfo.Name.ABSOLUTE_HUMIDITY)
        )

        neutron_column_name = (
            config.neutron_column_name
            if config.neutron_column_name is not None
            else str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)
        )

        air_pressure_column_name = (
            config.air_pressure_column_name
            if config.air_pressure_column_name is not None
            else str(ColumnInfo.Name.AIR_PRESSURE)
        )

        if config.value_avg_soil_organic_carbon:
            value_avg_soil_organic_carbon_water_equiv = (
                _create_water_equiv_soc(config.value_avg_soil_organic_carbon)
            )
        else:
            value_avg_soil_organic_carbon_water_equiv = None

        return cls(
            # Processing settings
            hours_of_data_around_calib=config.hours_of_data_around_calib,
            converge_accuracy=config.converge_accuracy,
            neutron_conversion_method=config.neutron_conversion_method,
            koehli_parameters=config.koehli_parameters,
            horizontal_weight_method=config.horizontal_weight_method,
            vertical_weight_method=config.vertical_weight_method,
            # Date/time settings
            calib_data_date_time_column_name=calib_data_date_time_column_name,
            calib_data_date_time_format=config.calib_data_date_time_format,
            # Resolved column names
            sample_depth_column=sample_depth_column,
            distance_column=distance_column,
            bulk_density_of_sample_column=bulk_density_of_sample_column,
            profile_id_column=profile_id_column,
            soil_moisture_gravimetric_column=soil_moisture_gravimetric_column,
            soil_organic_carbon_column=soil_organic_carbon_column,
            lattice_water_column=lattice_water_column,
            temperature_column=temperature_column,
            relative_humidity_column=relative_humidity_column,
            abs_air_humidity_column=abs_air_humidity_column,
            neutron_column_name=neutron_column_name,
            air_pressure_column_name=air_pressure_column_name,
            # Site average values
            value_avg_lattice_water=config.value_avg_lattice_water,
            value_avg_bulk_density=config.value_avg_bulk_density,
            value_avg_soil_organic_carbon=config.value_avg_soil_organic_carbon,
            value_avg_soil_organic_carbon_water_equiv=value_avg_soil_organic_carbon_water_equiv,
        )


def _ensure_date_time_index(
    data_frame: pd.DataFrame, context: CalibrationContext
):
    """
    Ensures datetime is properly set as index. If user already has datetime index,
    leave it alone. If datetime is a column, convert to datetime and set as index.

    Parameters
    ----------
    data_frame : pd.DataFrame
        Calibration or time series DataFrame
    context : CalibrationContext
        Context info

    Returns
    -------
    pd.DataFrame
        DataFrame with datetime index

    Raises
    ------
    ValueError
        If the expected datetime column is found neither as column nor index
    """
    target_col = context.calib_data_date_time_column_name
    if (
        (data_frame.index.name == target_col)
        or (
            hasattr(data_frame.index, "names")
            and target_col in data_frame.index.names
        )
        or (
            isinstance(data_frame.index, pd.DatetimeIndex)
            and target_col not in data_frame.columns
        )
    ):
        print(f"Datetime already set as index ('{target_col}'), leaving as-is")
        # Ensure it's datetime type if it isn't already
        if not isinstance(data_frame.index, pd.DatetimeIndex):
            data_frame.index = pd.to_datetime(
                data_frame.index,
                utc=True,
                dayfirst=True,
                format=context.calib_data_date_time_format,
            )
        return data_frame

    elif target_col in data_frame.columns:
        print(f"Converting '{target_col}' column to datetime index")
        data_frame[target_col] = pd.to_datetime(
            data_frame[target_col],
            utc=True,
            dayfirst=True,
            format=context.calib_data_date_time_format,
        )
        data_frame = data_frame.set_index(target_col)
        return data_frame

    else:
        available_cols = list(data_frame.columns)
        index_name = data_frame.index.name

        raise ValueError(
            f"Expected datetime column '{target_col}' not found as column or index. "
            f"Available columns: {available_cols}. "
            f"Index name: {index_name}. "
            f"Please specify the correct column name in CalibrationConfiguration using "
            f"calib_data_date_time_column_name parameter."
        )


class CalibrationStation:
    """
    Abstract which does the complete claibration steps. Can be used on
    its own, but is mainly designed to facilitate CRNSDataHub
    calibration. Simply include the calibration data, the time series
    data and the config object and run find_n0_value(), to return the
    optimum N0.
    """

    def __init__(
        self,
        calibration_data: pd.DataFrame,
        time_series_data: pd.DataFrame,
        config: CalibrationConfiguration,
    ):
        self.calibration_data = calibration_data
        self.time_series_data = (
            time_series_data.copy()
        )  # copy time series to avoid side effects
        self.context = CalibrationContext().from_config(config=config)

    def _collect_stats_for_magazine(self):
        self.number_calib_days = len(
            self.calibrator.return_output_dict_as_dataframe()
        )

    def find_n0_value(self):
        """
        Runs the full process to obtain an N0 estimate.

        Returns
        -------
        float
            N0 estimate after calibration.
        """
        # Prepare calibration data
        calib_prepper = PrepareCalibrationData(
            calibration_data_frame=self.calibration_data,
            context=self.context,
        )
        self.context = calib_prepper.prepare_calibration_data()

        # Prepare neutron data
        times_series_prepper = PrepareNeutronCorrectedData(
            corrected_neutron_data_frame=self.time_series_data,
            context=self.context,
        )
        self.context = times_series_prepper.extract_calibration_day_values()

        # Weight samples of sm
        self.calibrator = CalibrationWeightsCalculator(context=self.context)
        self.context = self.calibrator.apply_weighting_to_multiple_days()

        # Find optimal N0
        n0_finder = CalculateN0(context=self.context)
        optimal_n0 = n0_finder.find_optimal_N0()
        return optimal_n0

    def return_calibration_results_data_frame(self):
        """
        Returns the daily results as a data frame. When multiple days
        calibration is undertaken on each day. The outputs of this are
        saved and this method returns them for viewing.

        Returns
        -------
        pd.DataFrame
            data frame with the results in it.
        """
        return self.calibrator.return_output_dict_as_dataframe()

    def return_weighting_dataframe(self):
        """
        Returns the information about the weighting procedure

        Returns
        -------
        pd.DataFrame
            dataframe with weights
        """
        try:
            return self.context.weights_df
        except Exception as e:
            print(e)


class SampleProfile:

    latest_pid = 0

    def __init__(
        self,
        soil_moisture_gravimetric,
        depth,
        bulk_density,
        site_avg_bulk_density,
        site_avg_organic_carbon,
        site_avg_lattice_water,
        calibration_day,
        distance=1,
        lattice_water=None,
        soil_organic_carbon=None,
        pid=None,
    ):
        """
        Initialise SampleProfile instance.

        Parameters
        ----------
        soil_moisture_gravimetric : array
            array of soil moisture gravimetric values in g/g
        depth : array
            The depth of each soil moisture sample
        bulk_density : array
            bulk density of the samples in g/cm^3
        distance : int, optional
            distance of the profile from the sensor, by default 1
        lattice_water : array-like, optional
            Lattice water from the samples , by default 0
        soil_organic_carbon : int, optional
            _description_, by default 0
        pid : _type_, optional
            _description_, by default None
        """

        # Vector data
        if pid is None:
            SampleProfile.latest_pid += 1
            self.pid = SampleProfile.latest_pid
        else:
            self.pid = pid

        self.soil_moisture_gravimetric = np.array(soil_moisture_gravimetric)
        self.depth = np.array(depth)
        self.bulk_density = np.array(bulk_density)
        self.site_avg_bulk_density = site_avg_bulk_density
        self.calibration_day = calibration_day
        self.soil_organic_carbon = (
            np.array(soil_organic_carbon)
            if soil_organic_carbon is not None
            else np.zeros_like(soil_moisture_gravimetric)
        )
        self.site_avg_organic_carbon = site_avg_organic_carbon
        self.site_avg_organic_carbon_water_equiv = _create_water_equiv_soc(
            site_avg_organic_carbon
        )
        self.lattice_water = self.lattice_water = (
            np.array(lattice_water)
            if lattice_water is not None
            else np.zeros_like(soil_moisture_gravimetric)
        )
        self.site_avg_lattice_water = site_avg_lattice_water
        self.vertical_weights = np.ones_like(soil_moisture_gravimetric)
        self._calculate_sm_total_vol()
        self._calculate_sm_total_grv()

        self._distance = distance
        self.rescaled_distance = distance  # initialise as distance first
        self.sm_total_weighted_avg_grv = np.nan
        self.sm_total_weighted_avg_vol = np.nan
        self.horizontal_weight = 1  # intialise as 1

    @property
    def distance(self):
        return self._distance

    def _calculate_sm_total_vol(self):
        """
        Calculate total volumetric soil moisture.
        """
        # replace nan entries in bulk_density by the site average
        bd = np.where(
            np.isnan(self.bulk_density),
            self.site_avg_bulk_density,
            self.bulk_density,
        )
        self.sm_total_vol = self.soil_moisture_gravimetric * bd

    def _calculate_sm_total_grv(self):
        """
        Calculate total gravimetric soil moisture.
        """

        self.sm_total_grv = self.soil_moisture_gravimetric


class PrepareCalibrationData:
    """
    Prepares the calibration dataframe for processing.

    - ensures datetime index
    - splits multiple days into individual data frames
    - for each calibration day, converts data into a list of
      SampleProfiles
    - calculates site averages of key information (e.g., bulk density)
    - gap fills key info with averages when missing
    """

    def __init__(
        self,
        calibration_data_frame: pd.DataFrame,
        context: CalibrationContext,
    ):
        """
        Instantiate attributes

        Parameters
        ----------
        calibration_data_frame : pd.DataFrame
            The dataframe with the calibration sample data in it. If
            multiple calibration days are available these should be
            stacked in the same dataframe.
        """

        self.calibration_data_frame = calibration_data_frame
        self.context = context

    def _create_list_of_df(self, context: CalibrationContext):
        """
        Splits up the self.calibration_data_frame into individual data
        frames, where each data frame is a different calibration day.

        Parameters
        ----------
        context : CalibrationContext
            Context for calibration

        Returns
        -------
        context
            CalibrationContext
        """

        context.list_of_data_frames = [
            self.calibration_data_frame[
                self.calibration_data_frame.index == calibration_day
            ]
            for calibration_day in context.unique_calibration_days
        ]
        return context

    def _create_calibration_day_profiles(
        self,
        single_day_data_frame,
        context: CalibrationContext,
    ):
        """
        Returns a list of SampleProfile objects which have been created
        from a single calibration day data frame.

        Parameters
        ----------
        single_day_data_frame : pd.DataFrame
            DataFrame snipped during calibration period
        context : CalibrationContext
            Data for processing.

        Returns
        -------
        List of SampleProfiles
            A list of created SampleProfiles
        """
        calibration_day_profiles = []
        profile_ids = np.unique(
            single_day_data_frame[context.profile_id_column]
        )
        for pid in profile_ids:
            temp_df = single_day_data_frame[
                single_day_data_frame[context.profile_id_column] == pid
            ]
            soil_profile = self._create_individual_profile(
                pid=pid, profile_data_frame=temp_df, context=context
            )

            calibration_day_profiles.append(soil_profile)
        return calibration_day_profiles

    def _create_individual_profile(
        self,
        pid,
        profile_data_frame,
        context,
    ):
        """
        Creates a SampleProfile object from a individual profile
        dataframe

        Parameters
        ----------
        pid : numeric
            The profile ID to represent the profile.
        profile_data_frame : pd.DataFrame
            A data frame which holds the values for one single profile.
        context : CalibrationContext
            Information for processing

        Returns
        -------
        SampleProfile
            A SampleProfile object is returned.
        """
        distances = profile_data_frame[context.distance_column].median()
        depths = profile_data_frame[context.sample_depth_column]
        bulk_density = profile_data_frame[
            context.bulk_density_of_sample_column
        ]

        soil_moisture_gravimetric = profile_data_frame[
            context.soil_moisture_gravimetric_column
        ]

        soil_organic_carbon = profile_data_frame[
            context.soil_organic_carbon_column
        ]

        lattice_water = profile_data_frame[context.lattice_water_column]

        # only need one calibration datetime
        calibration_datetime = next(iter(profile_data_frame.index))

        soil_profile = SampleProfile(
            soil_moisture_gravimetric=soil_moisture_gravimetric,
            depth=depths,
            bulk_density=bulk_density,
            site_avg_bulk_density=context.value_avg_bulk_density,
            distance=distances,
            lattice_water=lattice_water,
            soil_organic_carbon=soil_organic_carbon,
            pid=pid,
            calibration_day=calibration_datetime,
            site_avg_lattice_water=context.value_avg_lattice_water,
            site_avg_organic_carbon=context.value_avg_soil_organic_carbon,
        )
        return soil_profile

    def _create_site_avg_bulk_density(self, context: CalibrationContext):
        """
        Produces a average bulk density from provided sample data, if
        not available uses user provided average, if thats not available
        raises error

        Returns
        -------
        float
            site average bulk density

        Raises
        ------
        ValueError
            No bulk density provided
        """
        if (
            context.bulk_density_of_sample_column
            not in self.calibration_data_frame.columns
        ):
            message = (
                "There appears to be no bulk density data in the calibration sample dataset. "
                "Attempting to use the provided site average..."
            )
            print(message)
            if context.value_avg_bulk_density is None:
                message = (
                    "There is no provided site average bulk density value. Please provide this "
                    "in sensor configuration files (if using configs), SensorInformation (if using notebooks)"
                    "or CalibrationConfiguration (if using calibration module directly.)"
                )
                raise ValueError(message)
            else:
                message = "Using the provided site average bulk density value."
                print(message)

        else:
            message = "Calculating site average bulk density from provided sample data."
            print(message)
            context.value_avg_bulk_density = self.calibration_data_frame[
                context.bulk_density_of_sample_column
            ].mean()

        return context

    def _create_site_avg_lattice_water(self, context: CalibrationContext):
        """
        Produces a average lattice water from provided sample data, if
        not available uses user provided average, if thats not available
        raises error. Adds info to context

        Returns
        -------
        context
            Context

        Raises
        ------
        ValueError
            No lattice water provided
        """
        if (
            context.lattice_water_column
            not in self.calibration_data_frame.columns
        ):
            message = (
                "There appears to be no lattice water data in the calibration sample dataset. "
                "Attempting to use the provided site average..."
            )
            print(message)
            if context.value_avg_lattice_water is None:
                message = (
                    "There is no provided site average lattice water value. Please provide this "
                    "in sensor configuration files (if using configs), SensorInformation (if using notebooks)"
                    "or CalibrationConfiguration (if using calibration module directly.)\n"
                    "NOTE: If you don't know, use 0"
                )
                raise ValueError(message)
            else:
                message = (
                    "Using the provided site average lattice water value."
                )
                print(message)

        else:
            message = "Calculating site average lattice water from provided sample data."
            print(message)
            context.value_avg_lattice_water = self.calibration_data_frame[
                context.lattice_water_column
            ].mean()
        return context

    def _create_site_avg_soil_organic_carbon(
        self, context: CalibrationContext
    ):
        """
        Produces a average soil_organic_carbon from provided sample
        data, if not available uses user provided average, if thats not
        available raises error

        Returns
        -------
        CalibrationContext
            site average soil_organic_carbon in context

        Raises
        ------
        ValueError
            No soil_organic_carbon provided
        """
        if (
            context.soil_organic_carbon_column
            not in self.calibration_data_frame.columns
        ):
            message = (
                "There appears to be no soil_organic_carbon data in the calibration sample dataset. "
                "Attempting to use the provided site average..."
            )
            print(message)
            if context.value_avg_soil_organic_carbon is None:
                message = (
                    "There is no provided site average soil_organic_carbon value. Please provide this "
                    "in sensor configuration files (if using configs), SensorInformation (if using notebooks)"
                    "or CalibrationConfiguration (if using calibration module directly.)\n"
                    "NOTE: If you don't know, use 0"
                )
                raise ValueError(message)
            else:
                message = "Using the provided site average soil_organic_carbon value."
                print(message)

        else:
            message = "Calculating site average soil_organic_carbon from provided sample data."
            print(message)

            context.value_avg_soil_organic_carbon = (
                self.calibration_data_frame[
                    context.soil_organic_carbon_column
                ].mean()
            )

        if np.isnan(context.value_avg_soil_organic_carbon):
            context.value_avg_soil_organic_carbon = 0

        context.value_avg_soil_organic_carbon_water_equiv = (
            _create_water_equiv_soc(context.value_avg_soil_organic_carbon)
        )

        return context

    def _create_site_avg_values(self, context: CalibrationContext):
        """
        Derives site avg values required for calibration

        Returns
        -------
        CalibrationContext
            more context
        """
        context = self._create_site_avg_bulk_density(context=context)
        context = self._create_site_avg_lattice_water(context=context)
        context = self._create_site_avg_soil_organic_carbon(context=context)
        return context

    def _parse_unique_calibration_days(
        self,
        context: CalibrationContext,
    ):
        """
        Parses unique calibration days and adds information to context

        Parameters
        ----------
        context : CalibrationContext
            DataContext for calibration

        Returns
        -------
        context
            CalibrationContext
        """
        context.unique_calibration_days = np.unique(
            self.calibration_data_frame.index
        )
        return context

    def _process_dfs_into_profiles(self, context: CalibrationContext):
        """
        Processes the calibration day data into profiles

        Parameters
        ----------
        context : CalibrationContext
            _description_

        Returns
        -------
        CalibrationContext
            context with profiles
        """

        for data_frame in context.list_of_data_frames:
            calibration_day_profiles = self._create_calibration_day_profiles(
                single_day_data_frame=data_frame,
                context=context,
            )
            context.list_of_profiles.extend(calibration_day_profiles)
        return context

    def prepare_calibration_data(self):
        """
        Prepares the calibration data into a list of profiles.
        """
        context = self.context
        self.calibration_data_frame = _ensure_date_time_index(
            data_frame=self.calibration_data_frame, context=context
        )

        context = self._parse_unique_calibration_days(context)
        context = self._create_site_avg_values(context)
        context = self._create_list_of_df(context=context)
        context = self._process_dfs_into_profiles(context=context)

        return context


class PrepareNeutronCorrectedData:

    def __init__(
        self,
        corrected_neutron_data_frame: pd.DataFrame,
        context: CalibrationConfiguration,
    ):
        self.corrected_neutron_data_frame = corrected_neutron_data_frame
        self.context = context

    def _ensure_abs_humidity_exists(self, data_frame: pd.DataFrame):
        """
        Checks to see if absolute humidity exists in the data frame. If
        it doesn't it will create it.

        Parameters
        ----------
        data_frame : pd.DataFrame
            Corrected neutron dataframe

        Returns
        -------
        pd.DataFrame
            Corrected neutron dataframe with abs humidity
        """
        if str(ColumnInfo.Name.ABSOLUTE_HUMIDITY) not in data_frame.columns:
            abs_humidity_creator = AbsoluteHumidityCreator(
                data_frame=data_frame
            )
            data_frame = abs_humidity_creator.check_and_return_abs_hum_column()
            return data_frame
        else:
            return data_frame

    def _uncorrect_humidity_for_koehli(
        self,
        data_frame: pd.DataFrame,
        context: CalibrationContext,
    ):
        """
        Uncorrect humidity from corrected neutrons if this was done and
        the koehli method is selected.

        NOTE: This occurs on a copy of the crns_data_frame (i.e., the
        changes are not maintained outside of the calibration stage). It
        will be uncorrected a second time later when the conversion to
        soil moisture happens, if required.

        Parameters
        ----------
        data_frame : pd.DataFrame
            DataFrame with data for processing
        context : _type_, optional
            context, by default CalibrationContext

        Returns
        -------
        pd.DataFrame
            DataFrame with either correction removed or not
        """
        if (
            context.neutron_conversion_method == "koehli_etal_2021"
            and str(ColumnInfo.Name.HUMIDITY_CORRECTION) in data_frame.columns
        ):
            data_frame[context.neutron_column_name] /= data_frame[
                str(ColumnInfo.Name.HUMIDITY_CORRECTION)
            ]
            return data_frame
        else:
            return data_frame

    def extract_calibration_day_values(self):
        """
        Extracts the rows of data for each calibration day.
        """

        context = self.context
        data_frame = self.corrected_neutron_data_frame
        data_frame = _ensure_date_time_index(
            data_frame=data_frame, context=context
        )
        data_frame = self._ensure_abs_humidity_exists(data_frame=data_frame)
        data_frame = self._uncorrect_humidity_for_koehli(
            data_frame=data_frame, context=context
        )

        calibration_indicies_dict = self._extract_calibration_day_indices(
            corrected_neutron_data_frame=data_frame, context=context
        )

        dict_of_data = {}
        for value in calibration_indicies_dict.values():
            tmp_df = data_frame.loc[value]
            calib_day = None
            # Find calibration day index to use as dict key
            for day in context.unique_calibration_days:
                calib_day = self._find_nearest_calib_day_in_indicies(
                    day=day, data_frame=tmp_df
                )
                if calib_day is not None:
                    break
            dict_of_data[calib_day] = tmp_df

        context.calib_day_df_dict = dict_of_data
        return context

    def _find_nearest_calib_day_in_indicies(self, day, data_frame):
        """
        Finds the nearest calibration day to the indices.

        Parameters
        ----------
        day : Timedelta
            _description_
        data_frame : pd.DataFrame
            dataframe of data

        Returns
        -------
        Timedelta
            Calibration day
        """

        day = pd.to_datetime(day)
        mask = (data_frame.index >= day - timedelta(hours=1)) & (
            data_frame.index <= day + timedelta(hours=1)
        )
        if mask.any():
            calib_day = day
            return calib_day

    def _extract_calibration_day_indices(
        self,
        corrected_neutron_data_frame,
        context: CalibrationContext,
    ):
        """
        Extracts the required indices

        Parameters
        ----------
        corrected_neutron_data_frame : pd.DataFrame
            DataFrame with corrected neutrons and meteorological data
        context : CalibrationContext
            Context for processing

        Returns
        -------
        dict
            A dictionary for each calibration date with the indices to
            extract from corrected neutron data.
        """
        extractor = IndicesExtractor(
            corrected_neutron_data_frame=corrected_neutron_data_frame,
            context=context,
        )
        calibration_indices = extractor.extract_calibration_day_indices()

        return calibration_indices


class IndicesExtractor:
    """
    Extracts indices from the corrected neutron data based on the
    supplied calibration days
    """

    def __init__(
        self,
        corrected_neutron_data_frame,
        context,
    ):
        """
        Attributes.

        Parameters
        ----------
        corrected_neutron_data_frame : pd.DataFrame
            The corrected neutron data frame
        calibration_data_prepper : PrepareCalibrationData
            The processed object
        hours_of_data_to_extract : int, optional
            The number of hours of data around the calibration date time
            stamp to collect., by default 6
        """
        self.corrected_neutron_data_frame = corrected_neutron_data_frame
        self.context = context

    def _convert_to_datetime(
        self,
        dates,
    ):
        """
        Convert a list of dates to pandas Timestamp objects.
        """
        return pd.to_datetime(dates)

    def _create_time_window(
        self,
        date: pd.Timestamp,
        context: CalibrationContext,
    ):
        """
        Create a time window around a given date.

        Parameters
        ----------
        date : pd.Timestamp
            Time stamp to create windows around
        context : CalibrationContext
            Context for processing

        Returns
        -------
        Timedelta, Timedelta
            Start and end Timedelta for calib window
        """
        half_window = context.hours_of_data_around_calib / 2
        window = pd.Timedelta(hours=half_window)
        return date - window, date + window

    def _extract_indices_within_window(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp,
        data_frame: pd.DataFrame,
    ):
        """
        Extract indices of data points within a given time window.

        Parameters
        ----------
        start : pd.Timestamp
            Start point
        end : pd.Timestamp
            End point
        data_frame : pd.DataFrame
            DataFrame

        Returns
        -------
        List
            Indexes in range
        """
        mask = (data_frame.index >= start) & (data_frame.index <= end)
        return data_frame.index[mask].tolist()

    def extract_calibration_day_indices(self):
        """
        Extract indices for each calibration day within a time window.

        Returns
        -------
        Dict
            Indicies for each calibration day
        """
        context = self.context
        unique_days = self._convert_to_datetime(
            context.unique_calibration_days
        )

        calibration_indices = {}
        for day in unique_days:
            start, end = self._create_time_window(
                date=day,
                context=context,
            )
            calibration_indices[day] = self._extract_indices_within_window(
                start=start,
                end=end,
                data_frame=self.corrected_neutron_data_frame,
            )

        return calibration_indices


class CalibrationWeightsCalculator:
    def __init__(
        self,
        context: CalibrationContext,
    ):
        self.context = context

    def _get_time_series_data_for_day(self, day):
        """
        Get data for particular day

        Parameters
        ----------
        day : Timedelta
            Day

        Returns
        -------
        _type_
            _description_
        """
        return self.context.calib_day_df_dict[day]

    @staticmethod
    def _initial_vol_sm_estimate(profiles: List):
        """
        Gets an initial equal average soil moisture estimate

        Parameters
        ----------
        profiles : List
            List of SampleProfiles

        Returns
        -------
        sm_estimate : float
            Estimate of field soil moisture
        """
        sm_total_vol_values = [
            np.array(profile.sm_total_vol).flatten()
            for profile in profiles
            if profile.sm_total_vol is not None
        ]
        flattened = np.concatenate(sm_total_vol_values)
        valid_values = flattened[~np.isnan(flattened)]
        sm_estimate = np.mean(valid_values)
        return sm_estimate

    def apply_weighting_to_multiple_days(self):
        """
        Applies the weighting procedure to multiple calibration days if
        present.

        Returns
        -------
        CalibrationContext
            With more context
        """

        context = self.context

        for day in context.unique_calibration_days:

            tmp_data = self._get_time_series_data_for_day(day)
            profiles = [
                p for p in context.list_of_profiles if p.calibration_day == day
            ]

            volumetric_sm_estimate = self._initial_vol_sm_estimate(
                profiles=profiles
            )
            average_abs_air_humidity = tmp_data[
                context.abs_air_humidity_column
            ].mean()
            average_air_pressure = tmp_data[
                context.air_pressure_column_name
            ].mean()
            average_neutron_count = tmp_data[
                context.neutron_column_name
            ].mean()

            field_average_sm_vol, field_average_sm_grav, footprint = (
                self.calculate_weighted_sm_average(
                    profiles=profiles,
                    initial_volumetric_sm_estimate=volumetric_sm_estimate,
                    average_abs_air_humidity=average_abs_air_humidity,
                    average_air_pressure=average_air_pressure,
                )
            )

            output = {
                "field_average_soil_moisture_volumetric": field_average_sm_vol,
                "field_average_soil_moisture_gravimetric": field_average_sm_grav,
                "average_neutron_count": average_neutron_count,
                "horizontal_footprint_radius_in_meters": footprint,
                "absolute_air_humidity": average_abs_air_humidity,
                "atmospheric_pressure": average_air_pressure,
            }

            context.calib_metrics_dict[day] = output

        context = self._sample_profiles_to_dataframe(context)
        return context

    def calculate_weighted_sm_average(
        self,
        profiles: List,
        initial_volumetric_sm_estimate: float,
        average_abs_air_humidity: float,
        average_air_pressure: float,
    ):
        """
        Calculates the field average soil moisture value according to
        Schrön et al., 2017. Weighting is calculated on volumetric soil
        moisture volumes (as described in the paper), but a weighted
        gravimetric value is given for calibration in neptoon.

        Parameters
        ----------
        profiles : List[Profile]
            A list of soil‐profile objects collected on the same day.
            Each Profile must have:
              - `.rescaled_distance` (rescaled distance from sensor, in
                m)
              - `.site_avg_bulk_density` (bulk density, in g/cm3)
              - `.depth` (array of depths, in cm)
              - `.sm_total_vol` (array of volumetric‐moisture values,
                cm3/cm3)
              - `.sm_total_grv` (array of gravimetric‐moisture values,
                g/g)
        initial_sm_estimate : float
            Initial soil moisture estimate (usually equal average)
        average_abs_air_humidity : float
            Average absolute air humidity
        average_air_pressure : float
            Air pressure average during calibration period (hPa)

        Returns
        -------
        field_average_sm_volumetric : float
            Converged volumetric soil moisture (cm3/cm3).
        field_average_sm_gravimetric : float
            Corresponding converged gravimetric soil moisture (g/g).
        footprint_m : float
            Estimated radius (m) of the footprint of the sensor.

        Notes
        -----
        - Convergence is checked via `abs((new_volumetric_estimate -
          old_estimate) / old_estimate) <
          self.config.converge_accuracy`.
        - Uses `Schroen2017.rescale_distance`,
          `Schroen2017.calculate_measurement_depth`,
          `Schroen2017.vertical_weighting`,
          `Schroen2017.horizontal_weighting`, and
          `Schroen2017.calculate_footprint_radius` at each iteration.

        """

        volumetric_sm_estimate = copy.deepcopy(initial_volumetric_sm_estimate)
        accuracy = 1
        field_average_sm_volumetric = None
        field_average_sm_gravimetric = None

        while accuracy > self.context.converge_accuracy:
            profile_sm_averages_volumetric = []
            profile_sm_averages_gravimetric = []
            profiles_horizontal_weights = []

            for p in profiles:

                p.rescaled_distance = Schroen2017.rescale_distance(
                    distance_from_sensor=p.rescaled_distance,
                    atmospheric_pressure=average_air_pressure,
                    volumetric_soil_moisture=volumetric_sm_estimate,
                )

                if self.context.vertical_weight_method == "equal":
                    p.vertical_weights = np.ones_like(
                        p.soil_moisture_gravimetric
                    )
                else:
                    p.vertical_weights = Schroen2017.vertical_weighting(
                        depth=p.depth,
                        distance=p.rescaled_distance,
                        bulk_density=p.site_avg_bulk_density,
                        volumetric_soil_moisture=volumetric_sm_estimate,
                    )
                    # Normalise
                    p.vertical_weights = p.vertical_weights / sum(
                        p.vertical_weights
                    )

                # Calculate weighted sm average
                p.sm_total_weighted_avg_vol = np.average(
                    p.sm_total_vol, weights=p.vertical_weights
                )
                p.sm_total_weighted_avg_grv = np.average(
                    p.sm_total_grv, weights=p.vertical_weights
                )
                if self.context.horizontal_weight_method == "equal":
                    p.horizontal_weight = 1
                else:
                    p.horizontal_weight = Schroen2017.horizontal_weighting(
                        distance=p.rescaled_distance,
                        volumetric_soil_moisture=p.sm_total_weighted_avg_vol,
                        abs_air_humidity=average_abs_air_humidity,
                    )

                # create a list of average sm and horizontal weights
                profile_sm_averages_volumetric.append(
                    p.sm_total_weighted_avg_vol
                )
                profile_sm_averages_gravimetric.append(
                    p.sm_total_weighted_avg_grv
                )
                profiles_horizontal_weights.append(p.horizontal_weight)

            # mask out nan values from list
            profile_sm_averages_volumetric = np.ma.MaskedArray(
                profile_sm_averages_volumetric,
                mask=np.isnan(profile_sm_averages_volumetric),
            )
            profile_sm_averages_gravimetric = np.ma.MaskedArray(
                profile_sm_averages_gravimetric,
                mask=np.isnan(profile_sm_averages_gravimetric),
            )
            profiles_horizontal_weights = np.ma.MaskedArray(
                profiles_horizontal_weights,
                mask=np.isnan(profiles_horizontal_weights),
            )

            # Normalise horizontal weights
            weight_sum = np.ma.sum(profiles_horizontal_weights)
            profiles_horizontal_weights = (
                profiles_horizontal_weights / weight_sum
            )
            for i, p in enumerate(profiles):
                p.horizontal_weight = profiles_horizontal_weights.data[i]

            # create field averages of soil moisture

            field_average_sm_volumetric = np.average(
                profile_sm_averages_volumetric,
                weights=profiles_horizontal_weights,
            )
            field_average_sm_gravimetric = np.average(
                profile_sm_averages_gravimetric,
                weights=profiles_horizontal_weights,
            )

            # check convergence accuracy
            if (
                self.context.vertical_weight_method == "schroen_etal_2017"
                and self.context.horizontal_weight_method
                == "schroen_etal_2017"
            ):
                accuracy = abs(
                    (field_average_sm_volumetric - volumetric_sm_estimate)
                    / volumetric_sm_estimate
                )
            else:
                # Stop convergence if any weighting left as equal
                accuracy = self.context.converge_accuracy

            if accuracy > self.context.converge_accuracy:

                volumetric_sm_estimate = copy.deepcopy(
                    field_average_sm_volumetric
                )
                profile_sm_averages_volumetric = []
                profile_sm_averages_gravimetric = []
                profiles_horizontal_weights = []

        footprint_m = Schroen2017.calculate_footprint_radius(
            volumetric_soil_moisture=field_average_sm_volumetric,
            abs_air_humidity=average_abs_air_humidity,
            atmospheric_pressure=average_air_pressure,
        )

        return (
            field_average_sm_volumetric,
            field_average_sm_gravimetric,
            footprint_m,
        )

    def return_output_dict_as_dataframe(self):
        """
        Returns the dictionary of information created for each
        calibration day during processing as a pandas DataFrame

        Returns
        -------
        pd.DataFrame
            DataFrame with information created during processing.
        """
        df = pd.DataFrame.from_dict(
            self.context.calib_metrics_dict, orient="index"
        )
        df = df.reset_index()
        df = df.rename(
            columns={
                "index": "calibration_day",
                "field_average_soil_moisture_volumetric": "field_average_soil_moisture_volumetric",
                "field_average_soil_moisture_gravimetric": "field_average_soil_moisture_gravimetric",
                "horizontal_footprint_in_meters": "horizontal_footprint_radius",
            }
        )
        return df

    def return_weighting_dataframe(self):
        """
        Returns the information about the weighting procedure

        Returns
        -------
        pd.DataFrame
            dataframe with weights
        """
        return self.context.weights_df

    def _get_array_attributes(self, profile) -> List[str]:
        """Get list of attributes that are arrays/lists."""
        array_attrs = []

        for attr_name in dir(profile):
            if attr_name.startswith("_") or callable(
                getattr(profile, attr_name)
            ):
                continue

            attr_value = getattr(profile, attr_name)
            if (
                isinstance(attr_value, (np.ndarray, list))
                and len(attr_value) > 1
            ):
                array_attrs.append(attr_name)

        return array_attrs

    def _get_scalar_attributes(self, profile) -> List[str]:
        """Get list of attributes that are scalar values."""
        scalar_attrs = []

        for attr_name in dir(profile):
            if attr_name.startswith("_") or callable(
                getattr(profile, attr_name)
            ):
                continue

            attr_value = getattr(profile, attr_name)
            if not isinstance(attr_value, (np.ndarray, list)) or (
                isinstance(attr_value, (np.ndarray, list))
                and len(attr_value) <= 1
            ):
                # Handle scalar numpy arrays
                if isinstance(attr_value, np.ndarray) and attr_value.size == 1:
                    scalar_attrs.append(attr_name)
                elif not isinstance(attr_value, (np.ndarray, list)):
                    scalar_attrs.append(attr_name)

        return scalar_attrs

    def _sample_profiles_to_dataframe(
        self,
        context: CalibrationContext,
    ):
        """
        Convert a list of SampleProfile objects to a pandas DataFrame.

        Creates a long-format DataFrame where each row represents one
        depth measurement. Scalar values from each profile are repeated
        for all depth measurements in that profile.

        Parameters
        ----------
        context: CalibrationContext
            Context which holds list of profiles

        Returns
        -------
        CalibrationContext
        """
        sample_profiles = context.list_of_profiles
        if not sample_profiles:
            return pd.DataFrame()

        all_rows = []

        for profile in sample_profiles:
            array_attrs = self._get_array_attributes(profile)
            scalar_attrs = self._get_scalar_attributes(profile)

            if not array_attrs:
                row_data = {
                    attr: getattr(profile, attr) for attr in scalar_attrs
                }
                all_rows.append(row_data)
            else:
                array_length = len(getattr(profile, array_attrs[0]))

                for i in range(array_length):
                    row_data = {}

                    for attr in scalar_attrs:
                        row_data[attr] = getattr(profile, attr)

                    for attr in array_attrs:
                        array_val = getattr(profile, attr)
                        row_data[attr] = (
                            array_val[i]
                            if isinstance(array_val, np.ndarray)
                            else array_val[i]
                        )

                    all_rows.append(row_data)

        context.weights_df = pd.DataFrame(all_rows)
        return context


class CalculateN0:
    def __init__(
        self,
        context: CalibrationContext | None = None,
    ):
        self.context = context
        self._using_custom_vals = False
        self._neutron_counts = None  # only used for custom inputs

    def set_values(
        self,
        soil_moisture: list,
        corrected_neutron_counts: list,
        conversion_method: Literal[
            "desilets_etal_2010", "koehli_etal_2021"
        ] = "desilets_etal_2010",
        lattice_water=0,
        water_equiv_soil_organic_carbon=0,
        absolute_humidity=None,
        koehli_parameters: Literal[
            "Jan23_uranos",
            "Jan23_mcnpfull",
            "Mar12_atmprof",
            "Mar21_mcnp_drf",
            "Mar21_mcnp_ewin",
            "Mar21_uranos_drf",
            "Mar21_uranos_ewin",
            "Mar22_mcnp_drf_Jan",
            "Mar22_mcnp_ewin_gd",
            "Mar22_uranos_drf_gd",
            "Mar22_uranos_ewin_chi2",
            "Mar22_uranos_drf_h200m",
            "Aug08_mcnp_drf",
            "Aug08_mcnp_ewin",
            "Aug12_uranos_drf",
            "Aug12_uranos_ewin",
            "Aug13_uranos_atmprof",
            "Aug13_uranos_atmprof2",
        ] = "Mar21_mcnp_drf",
    ):
        def _ensure_list(value, name):
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return [float(value)]
            if isinstance(value, list):
                return [float(x) for x in value]
            raise TypeError(
                f"{name} must be a number, list of numbers, or None"
            )

        soil_moisture = _ensure_list(soil_moisture, "soil_moisture")
        corrected_neutron_counts = _ensure_list(
            corrected_neutron_counts, "neutron_counts"
        )
        self._neutron_counts = corrected_neutron_counts
        if len(soil_moisture) != len(corrected_neutron_counts):
            raise ValueError(
                f"soil_moisture and neutron_count must have the same length. "
                f"Got {len(soil_moisture)} and {len(corrected_neutron_counts)} respectively."
            )

        if absolute_humidity is None:
            absolute_humidity = [0.0] * len(soil_moisture)
        else:
            absolute_humidity = _ensure_list(
                absolute_humidity, "absolute_humidity"
            )
            if len(absolute_humidity) != len(corrected_neutron_counts):
                raise ValueError(
                    f"absolute_humidity and neutron_count must have the same length. "
                    f"Got {len(soil_moisture)} and {len(corrected_neutron_counts)} respectively."
                )

        metrics_dict = {}
        for i in range(len(soil_moisture)):
            output = {
                "field_average_soil_moisture_gravimetric": soil_moisture[i],
                "average_neutron_count": corrected_neutron_counts[i],
                "absolute_air_humidity": absolute_humidity[i],
            }
            metrics_dict[i] = output

        self.context = CalibrationContext(
            neutron_conversion_method=conversion_method,
            value_avg_lattice_water=lattice_water,
            value_avg_soil_organic_carbon_water_equiv=water_equiv_soil_organic_carbon,
            koehli_parameters=koehli_parameters,
            calib_metrics_dict=metrics_dict,
        )
        self._using_custom_vals = True

    def _find_optimal_n0_single_day_desilets_etal_2010(
        self,
        gravimetric_sm_on_day,
        neutron_mean,
        n0_range: pd.Series,
        lattice_water=0,
        water_equiv_soil_organic_carbon=0,
    ):
        """
        Finds optimal N0 number when using desilets et al., 2010 method

        Parameters
        ----------
        gravimetric_sm_on_day : float
            gravimetric soil moisture (weighted)
        neutron_mean : float
            average (corrected) neutron count

        Returns
        -------
        float
            N0
        """

        gravimetric_sm_on_day_total = (
            gravimetric_sm_on_day
            + lattice_water
            + water_equiv_soil_organic_carbon
        )

        def calculate_sm_and_error_desilets(n0):
            sm_prediction = (
                neutrons_to_total_grav_soil_moisture_desilets_etal_2010(
                    neutron_count=neutron_mean,
                    n0=n0,
                )
            )
            rel_error = (
                abs(sm_prediction - gravimetric_sm_on_day_total)
            ) / gravimetric_sm_on_day_total

            return pd.Series(
                {
                    "N0": n0,
                    "soil_moisture_prediction": sm_prediction,
                    "relative_error": rel_error,
                }
            )

        results_df = n0_range.apply(calculate_sm_and_error_desilets)
        return results_df

    def _find_optimal_n0_single_day_koehli_etal_2021(
        self,
        gravimetric_sm_on_day: float,
        neutron_mean: float,
        n0_range: pd.Series,
        abs_air_humidity: float,
        lattice_water: float,
        water_equiv_soil_organic_carbon: float,
        koehli_parameters: str,
    ):
        """
        Finds optimal N0 number when using Koehli etal method

        Parameters
        ----------
        gravimetric_sm_on_day : float
            Average gravimetic water on calibration day)
        neutron_mean : float | int
            Mean corrected neutron count
        abs_air_humidity : float
            Absolute air humidity
        lattice_water : float
            Lattice water content of soil
        water_equiv_soil_organic_carbon : float
            water equivelant of soil organic carbon
        koehli_parameters: str
            The specific method form of Koehli method

        Returns
        -------
        Tuple
            The N0 calibration term and absolute error (dummy nan value)
        """
        gravimetric_sm_on_day_total = (
            gravimetric_sm_on_day
            + lattice_water
            + water_equiv_soil_organic_carbon
        )

        def calculate_sm_and_error_koehli(n0):

            sm_prediction = neutrons_to_total_grav_soil_moisture_koehli_etal_2021(
                neutron_count=neutron_mean,
                n0=n0,
                abs_air_humidity=abs_air_humidity,
                lattice_water=lattice_water,
                water_equiv_soil_organic_carbon=water_equiv_soil_organic_carbon,
                koehli_parameters=koehli_parameters,
            )
            rel_error = (
                abs(sm_prediction - gravimetric_sm_on_day_total)
            ) / gravimetric_sm_on_day_total

            return pd.Series(
                {
                    "N0": n0,
                    "soil_moisture_prediction": sm_prediction,
                    "relative_error": rel_error,
                }
            )

        results_df = n0_range.apply(calculate_sm_and_error_koehli)
        return results_df

    def _create_n0_range(
        self,
        context: CalibrationContext,
        custom_range=False,
        neutron_counts=None,
    ):
        """
        Create a range of n0

        Parameters
        ----------
        context : CalibrationContext
            _description_

        Returns
        -------
        _type_
            _description_
        """
        if custom_range:
            total_neutron_mean = statistics.mean(neutron_counts)
        else:
            all_neutron_values = []
            for day in context.calib_metrics_dict.keys():
                day_neutrons = context.calib_day_df_dict[day][
                    context.neutron_column_name
                ]
                all_neutron_values.extend(day_neutrons.values)

            total_neutron_mean = pd.Series(all_neutron_values).mean()

        n0_range = pd.Series(
            range(int(total_neutron_mean), int(total_neutron_mean * 2.5))
        )
        return n0_range

    def find_optimal_N0(self):
        """
        Finds the optimal N0 number for the site using the weighted
        field average soil mositure.

        Returns
        -------
        average_n0
            The optimal n0 across all the supplied calibration days.
        """
        # Create neutron range
        context = self.context

        if self._using_custom_vals:
            n0_range = self._create_n0_range(
                context=context,
                custom_range=True,
                neutron_counts=self._neutron_counts,
            )
        else:
            n0_range = self._create_n0_range(context=context)

        lattice_water = context.value_avg_lattice_water
        water_equiv_soil_organic_carbon = (
            context.value_avg_soil_organic_carbon_water_equiv
        )
        context.calibration_results_by_day = {}

        for day, metrics in context.calib_metrics_dict.items():

            neutron_mean = metrics["average_neutron_count"]
            grav_sm = metrics["field_average_soil_moisture_gravimetric"]

            if context.neutron_conversion_method == "desilets_etal_2010":
                df_calib = self._find_optimal_n0_single_day_desilets_etal_2010(
                    gravimetric_sm_on_day=grav_sm,
                    neutron_mean=neutron_mean,
                    n0_range=n0_range,
                    lattice_water=lattice_water,
                    water_equiv_soil_organic_carbon=water_equiv_soil_organic_carbon,
                )

            elif context.neutron_conversion_method == "koehli_etal_2021":

                df_calib = self._find_optimal_n0_single_day_koehli_etal_2021(
                    gravimetric_sm_on_day=grav_sm,
                    neutron_mean=neutron_mean,
                    n0_range=n0_range,
                    abs_air_humidity=metrics["absolute_air_humidity"],
                    lattice_water=lattice_water,
                    water_equiv_soil_organic_carbon=water_equiv_soil_organic_carbon,
                    koehli_parameters=context.koehli_parameters,
                )
            context.calibration_results_by_day[day] = df_calib

        first_day = next(iter(context.calibration_results_by_day))
        total_error_df = pd.DataFrame(
            {"N0": context.calibration_results_by_day[first_day]["N0"]}
        )
        total_error_df["total_error"] = 0
        day_count = 0
        for day_df in context.calibration_results_by_day.values():
            total_error_df["total_error"] += day_df["relative_error"]
            day_count += 1

        new_total_error_col_name = f"total_error_from_{day_count}_calib_days"
        total_error_df.rename(
            {"total_error": new_total_error_col_name},
            axis=1,
            inplace=True,
        )
        min_error_idx = total_error_df[new_total_error_col_name].idxmin()
        n0_optimal = total_error_df.loc[min_error_idx, "N0"]
        return n0_optimal
