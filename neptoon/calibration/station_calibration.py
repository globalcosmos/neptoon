import pandas as pd
import numpy as np
import copy
from datetime import timedelta
from typing import Literal, List

# from scipy.optimize import minimize
from neptoon.columns import ColumnInfo
from neptoon.corrections import (
    Schroen2017,
    neutrons_to_total_grav_soil_moisture_desilets_etal_2010,
)
from neptoon.corrections.theory.neutrons_to_soil_moisture import (
    compute_n0_koehli_etal_2021,
)
from neptoon.data_prep.conversions import AbsoluteHumidityCreator


def _create_water_equiv_soc(soil_organic_carbon: float):
    return soil_organic_carbon * 0.555


class CalibrationConfiguration:
    """
    Configuration class for calibration steps
    """

    def __init__(
        self,
        hours_of_data_around_calib: int = 6,
        converge_accuracy: float = 0.01,
        neutron_conversion_method: Literal[
            "desilets_etal_2010", "koehli_etal_2021"
        ] = "desilets_etal_2010",
        calib_data_date_time_column_name: str = str(ColumnInfo.Name.DATE_TIME),
        calib_data_date_time_format: str = "%Y-%m-%d %H:%M",
        sample_depth_column: str = str(ColumnInfo.Name.CALIB_DEPTH_OF_SAMPLE),
        distance_column: str = str(ColumnInfo.Name.CALIB_DISTANCE_TO_SENSOR),
        bulk_density_of_sample_column: str = str(
            ColumnInfo.Name.CALIB_BULK_DENSITY
        ),
        profile_id_column: str = str(ColumnInfo.Name.CALIB_PROFILE_ID),
        soil_moisture_gravimetric_column: str = str(
            ColumnInfo.Name.CALIB_SOIL_MOISTURE_GRAVIMETRIC
        ),
        soil_organic_carbon_column: str = str(
            ColumnInfo.Name.CALIB_SOIL_ORGANIC_CARBON
        ),
        lattice_water_column: str = str(ColumnInfo.Name.CALIB_LATTICE_WATER),
        abs_air_humidity_column: str = str(ColumnInfo.Name.ABSOLUTE_HUMIDITY),
        neutron_column_name: str = str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ),
        air_pressure_column_name: str = str(ColumnInfo.Name.AIR_PRESSURE),
        value_avg_lattice_water: float = 0,
        value_avg_bulk_density: float = 0,
        value_avg_soil_organic_carbon: float = 0,
        koehli_method_form: Literal[
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
        ] = "Mar21_uranos_drf",
    ):
        """
        Attributes.

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
        calib_data_date_time_column_name : str, optional
            The name of the column containing date‐time information for
            each calibration day. By default, this is set to
            str(ColumnInfo.Name.DATE_TIME).
        sample_depth_column : str, optional
            The name of the column with sample depth values (cm), by
            default str(ColumnInfo.Name.CALIB_DEPTH_OF_SAMPLE)
        distance_column : str, optional
            The name of the column stating the distance of the sample
            from the sensor (meters), by default
            str(ColumnInfo.Name.CALIB_DISTANCE_TO_SENSOR)
        bulk_density_of_sample_column : str, optional
            The name of the column with bulk density values of the
            samples (g/cm^3), by default str(
            ColumnInfo.Name.CALIB_BULK_DENSITY )
        profile_id_column : str, optional
            Name of the column with profile IDs, by default
            str(ColumnInfo.Name.CALIB_PROFILE_ID)
        soil_moisture_gravimetric_column : str, optional
            Name of the column with gravimetric soil moisture values
            (g/g), by default str(
            ColumnInfo.Name.CALIB_SOIL_MOISTURE_GRAVIMETRIC )
        soil_organic_carbon_column : str, optional
            Name of the column with soil organic carbon values (g/g), by
            default str( ColumnInfo.Name.CALIB_SOIL_ORGANIC_CARBON )
        lattice_water_column : str, optional
            Name of the column with lattice water values (g/g), by
            default str(ColumnInfo.Name.CALIB_LATTICE_WATER)
        abs_air_humidity_column : str, optional
            Name of the column with absolute air humidity values
            (g/cm3), by default str(ColumnInfo.Name.ABSOLUTE_HUMIDITY)
        neutron_column_name : str, optional
            Name of the column with corrected neutrons in it, by default
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)
        air_pressure_column_name : str, optional
            Name of the column with air pressure vlaues in it, by
            default str(ColumnInfo.Name.AIR_PRESSURE)
        value_avg_lattice_water: float, optional
            The actual site average lattice water value
        value_avg_bulk_density: float, optional
            The actual site average dry soil bulk density
        value_avg_soil_organic_carbon: float, optional
            The actual site average soil organic carbon
        """
        self.hours_of_data_around_calib = hours_of_data_around_calib
        self.converge_accuracy = converge_accuracy
        self.calib_data_date_time_column_name = (
            calib_data_date_time_column_name
        )
        self.neutron_conversion_method = neutron_conversion_method
        self.calib_data_date_time_format = calib_data_date_time_format
        self.sample_depth_column = sample_depth_column
        self.distance_column = distance_column
        self.bulk_density_of_sample_column = bulk_density_of_sample_column
        self.profile_id_column = profile_id_column
        self.soil_moisture_gravimetric_column = (
            soil_moisture_gravimetric_column
        )
        self.soil_organic_carbon_column = soil_organic_carbon_column
        self.lattice_water_column = lattice_water_column
        self.abs_air_humidity_column = abs_air_humidity_column
        self.neutron_column_name = neutron_column_name
        self.air_pressure_column_name = air_pressure_column_name
        self.value_avg_lattice_water = value_avg_lattice_water
        self.value_avg_bulk_density = value_avg_bulk_density
        self.value_avg_soil_organic_carbon = value_avg_soil_organic_carbon
        self.value_avg_soil_organic_carbon_water_equiv = (
            _create_water_equiv_soc(value_avg_soil_organic_carbon)
        )
        self.koehli_method_form = koehli_method_form


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
        self.time_series_data = time_series_data
        self.config = config
        # place holders
        self.calib_prepper = None
        self.times_series_prepper = None
        self.calibrator = None

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
        self.calib_prepper = PrepareCalibrationData(
            calibration_data_frame=self.calibration_data,
            config=self.config,
        )
        self.calib_prepper.prepare_calibration_data()
        times_series_prepper = PrepareNeutronCorrectedData(
            corrected_neutron_data_frame=self.time_series_data,
            calibration_data_prepper=self.calib_prepper,
            config=self.config,
        )
        times_series_prepper.extract_calibration_day_values()
        self.calibrator = CalibrationWeightsCalculator(
            time_series_data_object=times_series_prepper,
            calib_data_object=self.calib_prepper,
            config=self.config,
        )
        self.calibrator.apply_weighting_to_multiple_days()
        optimal_n0 = self.calibrator.find_optimal_N0()
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
        self.D86 = np.nan
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
        config: CalibrationConfiguration,
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
        self.config = config
        self._ensure_date_time_index()

        self.unique_calibration_days = np.unique(
            self.calibration_data_frame[
                self.config.calib_data_date_time_column_name
            ]
        )
        self.list_of_data_frames = []
        self.list_of_profiles = []

    def _ensure_date_time_index(self):
        """
        Converts the date time column so the values are datetime type.
        """

        self.calibration_data_frame[
            self.config.calib_data_date_time_column_name
        ] = pd.to_datetime(
            self.calibration_data_frame[
                self.config.calib_data_date_time_column_name
            ],
            utc=True,
            dayfirst=True,
            format=self.config.calib_data_date_time_format,
        )

    def _create_list_of_df(self):
        """
        Splits up the self.calibration_data_frame into individual data
        frames, where each data frame is a different calibration day.
        """

        self.list_of_data_frames = [
            self.calibration_data_frame[
                self.calibration_data_frame[
                    self.config.calib_data_date_time_column_name
                ]
                == calibration_day
            ]
            for calibration_day in self.unique_calibration_days
        ]

    def _create_calibration_day_profiles(
        self,
        single_day_data_frame,
        site_avg_bulk_density,
        site_avg_lattice_water,
        site_avg_organic_carbon,
    ):
        """
        Returns a list of SampleProfile objects which have been created
        from a single calibration day data frame.

        Parameters
        ----------
        single_day_data_frame : pd.DataFrame
            _description_

        Returns
        -------
        List of SampleProfiles
            A list of created SampleProfiles
        """
        calibration_day_profiles = []
        profile_ids = np.unique(
            single_day_data_frame[self.config.profile_id_column]
        )
        for pid in profile_ids:
            temp_df = single_day_data_frame[
                single_day_data_frame[self.config.profile_id_column] == pid
            ]
            soil_profile = self._create_individual_profile(
                pid=pid,
                profile_data_frame=temp_df,
                site_avg_bulk_density=site_avg_bulk_density,
                site_avg_lattice_water=site_avg_lattice_water,
                site_avg_organic_carbon=site_avg_organic_carbon,
            )

            calibration_day_profiles.append(soil_profile)
        return calibration_day_profiles

    def _create_individual_profile(
        self,
        pid,
        profile_data_frame,
        site_avg_bulk_density,
        site_avg_lattice_water,
        site_avg_organic_carbon,
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

        Returns
        -------
        SampleProfile
            A SampleProfile object is returned.
        """
        distances = profile_data_frame[self.config.distance_column].median()
        depths = profile_data_frame[self.config.sample_depth_column]
        bulk_density = profile_data_frame[
            self.config.bulk_density_of_sample_column
        ]

        soil_moisture_gravimetric = profile_data_frame[
            self.config.soil_moisture_gravimetric_column
        ]

        soil_organic_carbon = profile_data_frame[
            self.config.soil_organic_carbon_column
        ]

        lattice_water = profile_data_frame[self.config.lattice_water_column]
        # only need one calibration datetime
        calibration_datetime = profile_data_frame[
            self.config.calib_data_date_time_column_name
        ].iloc[0]
        soil_profile = SampleProfile(
            soil_moisture_gravimetric=soil_moisture_gravimetric,
            depth=depths,
            bulk_density=bulk_density,
            site_avg_bulk_density=site_avg_bulk_density,
            distance=distances,
            lattice_water=lattice_water,
            soil_organic_carbon=soil_organic_carbon,
            pid=pid,
            calibration_day=calibration_datetime,
            site_avg_lattice_water=site_avg_lattice_water,
            site_avg_organic_carbon=site_avg_organic_carbon,
        )
        return soil_profile

    def _create_site_avg_bulk_density(self):
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
            self.config.bulk_density_of_sample_column
            not in self.calibration_data_frame.columns
        ):
            message = (
                "There appears to be no bulk density data in the calibration sample dataset. "
                "Attempting to use the provided site average..."
            )
            print(message)
            if self.config.value_avg_bulk_density is None:
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
            return self.calibration_data_frame[
                self.config.bulk_density_of_sample_column
            ].mean()

    def _create_site_avg_lattice_water(self):
        """
        Produces a average lattice water from provided sample data, if
        not available uses user provided average, if thats not available
        raises error

        Returns
        -------
        float
            site average lattice water

        Raises
        ------
        ValueError
            No lattice water provided
        """
        if (
            self.config.lattice_water_column
            not in self.calibration_data_frame.columns
        ):
            message = (
                "There appears to be no lattice water data in the calibration sample dataset. "
                "Attempting to use the provided site average..."
            )
            print(message)
            if self.config.value_avg_lattice_water is None:
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
            return self.calibration_data_frame[
                self.config.lattice_water_column
            ].mean()

    def _create_site_avg_soil_organic_carbon(self):
        """
        Produces a average soil_organic_carbon from provided sample
        data, if not available uses user provided average, if thats not
        available raises error

        Returns
        -------
        float
            site average soil_organic_carbon

        Raises
        ------
        ValueError
            No soil_organic_carbon provided
        """
        if (
            self.config.soil_organic_carbon_column
            not in self.calibration_data_frame.columns
        ):
            message = (
                "There appears to be no soil_organic_carbon data in the calibration sample dataset. "
                "Attempting to use the provided site average..."
            )
            print(message)
            if self.config.value_avg_soil_organic_carbon is None:
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

            return self.calibration_data_frame[
                self.config.soil_organic_carbon_column
            ].mean()

    def prepare_calibration_data(self):
        """
        Prepares the calibration data into a list of profiles.
        """

        self.config.value_avg_bulk_density = (
            self._create_site_avg_bulk_density()
        )

        self.config.value_avg_lattice_water = (
            self._create_site_avg_lattice_water()
        )

        self.config.value_avg_soil_organic_carbon = (
            self.calibration_data_frame[
                self.config.soil_organic_carbon_column
            ].mean()
        )

        if np.isnan(self.config.value_avg_soil_organic_carbon):
            self.config.value_avg_soil_organic_carbon = 0

        self._create_list_of_df()

        for data_frame in self.list_of_data_frames:
            calibration_day_profiles = self._create_calibration_day_profiles(
                single_day_data_frame=data_frame,
                site_avg_bulk_density=self.config.value_avg_bulk_density,
                site_avg_organic_carbon=self.config.value_avg_soil_organic_carbon,
                site_avg_lattice_water=self.config.value_avg_lattice_water,
            )
            self.list_of_profiles.extend(calibration_day_profiles)


class PrepareNeutronCorrectedData:

    def __init__(
        self,
        corrected_neutron_data_frame: pd.DataFrame,
        calibration_data_prepper: PrepareCalibrationData,
        config: CalibrationConfiguration,
    ):
        self.corrected_neutron_data_frame = corrected_neutron_data_frame
        self.calibration_data_prepper = calibration_data_prepper
        self.config = config
        self.data_dict = {}

        self._ensure_date_time_index()
        self._ensure_abs_humidity_exists()

    def _ensure_date_time_index(self):
        """
        Converts the date time column so the values are datetime type.
        """

        self.corrected_neutron_data_frame.index = pd.to_datetime(
            self.corrected_neutron_data_frame.index,
            utc=True,
        )

    def _ensure_abs_humidity_exists(self):
        """
        Checks to see if absolute humidity exists in the data frame. If
        it doesn't it will create it.
        """
        if (
            str(ColumnInfo.Name.ABSOLUTE_HUMIDITY)
            not in self.corrected_neutron_data_frame.columns
        ):
            abs_humidity_creator = AbsoluteHumidityCreator(
                self.corrected_neutron_data_frame
            )
            self.corrected_neutron_data_frame = (
                abs_humidity_creator.check_and_return_abs_hum_column()
            )

    def extract_calibration_day_values(self):
        """
        Extracts the rows of data for each calibration day.
        """
        calibration_indicies_dict = self._extract_calibration_day_indices(
            hours_of_data=self.config.hours_of_data_around_calib
        )
        dict_of_data = {}
        for value in calibration_indicies_dict.values():
            tmp_df = self.corrected_neutron_data_frame.loc[value]
            calib_day = None
            # Find calibration day index to use as dict key
            for day in self.calibration_data_prepper.unique_calibration_days:
                calib_day = self._find_nearest_calib_day_in_indicies(
                    day=day, data_frame=tmp_df
                )
                if calib_day is not None:
                    break
            dict_of_data[calib_day] = tmp_df

        self.data_dict = dict_of_data

    def _find_nearest_calib_day_in_indicies(self, day, data_frame):

        day = pd.to_datetime(day)
        mask = (data_frame.index >= day - timedelta(hours=1)) & (
            data_frame.index <= day + timedelta(hours=1)
        )
        if mask.any():
            calib_day = day
            return calib_day

    def _extract_calibration_day_indices(
        self,
        hours_of_data=6,
    ):
        """
        Extracts the required indices

        Parameters
        ----------
        hours_of_data : int, optional
            The hours of data around the calibration time stampe to
            collect, by default 6

        Returns
        -------
        dict
            A dictionary for each calibration date with the indices to
            extract from corrected neutron data.
        """
        extractor = IndicesExtractor(
            corrected_neutron_data_frame=self.corrected_neutron_data_frame,
            calibration_data_prepper=self.calibration_data_prepper,
            hours_of_data_to_extract=hours_of_data,
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
        calibration_data_prepper,
        hours_of_data_to_extract=6,
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
        self.calibration_data_prepper = calibration_data_prepper
        self.hours_of_data_to_extract = hours_of_data_to_extract

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
    ):
        """
        Create a time window around a given date.
        """
        half_window = self.hours_of_data_to_extract / 2
        window = pd.Timedelta(hours=half_window)
        return date - window, date + window

    def _extract_indices_within_window(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ):
        """
        Extract indices of data points within a given time window.
        """
        mask = (self.corrected_neutron_data_frame.index >= start) & (
            self.corrected_neutron_data_frame.index <= end
        )
        return self.corrected_neutron_data_frame.index[mask].tolist()

    def extract_calibration_day_indices(self):
        """
        Extract indices for each calibration day within a 6-hour window.
        """
        unique_days = self._convert_to_datetime(
            self.calibration_data_prepper.unique_calibration_days
        )

        calibration_indices = {}
        for day in unique_days:
            start, end = self._create_time_window(day)
            calibration_indices[day] = self._extract_indices_within_window(
                start, end
            )

        return calibration_indices


class CalibrationWeightsCalculator:
    def __init__(
        self,
        time_series_data_object: PrepareNeutronCorrectedData,
        calib_data_object: PrepareCalibrationData,
        config: CalibrationConfiguration,
    ):
        self.time_series_data_object = time_series_data_object
        self.calib_data_object = calib_data_object
        self.config = config

        self.calib_metrics_dict = {}

    def _get_time_series_data_for_day(
        self,
        day,
    ):
        return self.time_series_data_object.data_dict[day]

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
        """

        for day in self.calib_data_object.unique_calibration_days:

            tmp_data = self._get_time_series_data_for_day(day)
            profiles = [
                p
                for p in self.calib_data_object.list_of_profiles
                if p.calibration_day == day
            ]

            volumetric_sm_estimate = self._initial_vol_sm_estimate(
                profiles=profiles
            )
            average_abs_air_humidity = tmp_data[
                self.config.abs_air_humidity_column
            ].mean()
            average_air_pressure = tmp_data[
                self.config.air_pressure_column_name
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
                "horizontal_footprint_radius_in_meters": footprint,
                "absolute_air_humidity": average_abs_air_humidity,
                "atmospheric_pressure": average_air_pressure,
            }

            self.calib_metrics_dict[day] = output

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

        while accuracy > self.config.converge_accuracy:
            profile_sm_averages_volumetric = []
            profile_sm_averages_gravimetric = []
            profiles_horizontal_weights = []

            for p in profiles:

                p.rescaled_distance = Schroen2017.rescale_distance(
                    distance_from_sensor=p.rescaled_distance,
                    atmospheric_pressure=average_air_pressure,
                    volumetric_soil_moisture=volumetric_sm_estimate,
                )

                p.D86 = Schroen2017.calculate_measurement_depth(
                    distance=p.rescaled_distance,
                    bulk_density=p.site_avg_bulk_density,
                    volumetric_soil_moisture=volumetric_sm_estimate,
                )

                p.vertical_weights = Schroen2017.vertical_weighting(
                    depth=p.depth,
                    distance=p.rescaled_distance,
                    bulk_density=p.site_avg_bulk_density,
                    volumetric_soil_moisture=volumetric_sm_estimate,
                )

                # Calculate weighted sm average
                p.sm_total_weighted_avg_vol = np.average(
                    p.sm_total_vol, weights=p.vertical_weights
                )
                p.sm_total_weighted_avg_grv = np.average(
                    p.sm_total_grv, weights=p.vertical_weights
                )

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
            accuracy = abs(
                (field_average_sm_volumetric - volumetric_sm_estimate)
                / volumetric_sm_estimate
            )
            if accuracy > self.config.converge_accuracy:

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
        df = pd.DataFrame.from_dict(self.calib_metrics_dict, orient="index")
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

    def _find_optimal_N0_single_day_desilets_etal_2010(
        self,
        gravimetric_sm_on_day,
        neutron_mean,
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

        n0_range = pd.Series(range(int(neutron_mean), int(neutron_mean * 2.5)))
        gravimetric_sm_on_day_total = (
            gravimetric_sm_on_day
            + lattice_water
            + water_equiv_soil_organic_carbon
        )

        def calculate_sm_and_error(n0):
            sm_prediction = (
                neutrons_to_total_grav_soil_moisture_desilets_etal_2010(
                    neutrons=neutron_mean,
                    n0=n0,
                )
            )
            absolute_error = abs(sm_prediction - gravimetric_sm_on_day_total)
            return pd.Series(
                {
                    "N0": n0,
                    "soil_moisture_prediction": sm_prediction,
                    "absolute_error": absolute_error,
                }
            )

        results_df = n0_range.apply(calculate_sm_and_error)
        min_error_idx = results_df["absolute_error"].idxmin()
        n0_optimal = results_df.loc[min_error_idx, "N0"]
        minimum_error = results_df.loc[min_error_idx, "absolute_error"]
        return n0_optimal, minimum_error

    def _find_optimal_n0_single_day_koehli_etal_2021(
        self,
        gravimetric_sm_on_day: float,
        neutron_mean: int,
        abs_air_humidity: float,
        lattice_water: float,
        water_equiv_soil_organic_carbon: float,
        koehli_method_form: str,
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
        koehli_method_form: str
            The specific method form of Koehli method

        Returns
        -------
        Tuple
            The N0 calibration term and absolute error (dummy nan value)
        """
        n0 = compute_n0_koehli_etal_2021(
            gravimetric_sm=gravimetric_sm_on_day,
            neutron_count=neutron_mean,
            air_humidity=abs_air_humidity,
            lattice_water=lattice_water,
            water_equiv_soil_organic_carbon=water_equiv_soil_organic_carbon,
            koehli_method_form=koehli_method_form,
        )
        return n0, "nan"

    def find_optimal_N0(
        self,
    ):
        """
        Finds the optimal N0 number for the site using the weighted
        field average soil mositure.

        Returns
        -------
        average_n0
            The optimal n0 across all the supplied calibration days.
        """

        for day, metrics in self.calib_metrics_dict.items():
            neutron_mean = self.time_series_data_object.data_dict[day][
                self.config.neutron_column_name
            ].mean()
            grav_sm = metrics["field_average_soil_moisture_gravimetric"]

            if self.config.neutron_conversion_method == "desilets_etal_2010":
                n0_opt, abs_error = (
                    self._find_optimal_N0_single_day_desilets_etal_2010(
                        gravimetric_sm_on_day=grav_sm,
                        neutron_mean=neutron_mean,
                        lattice_water=self.config.value_avg_lattice_water,
                        water_equiv_soil_organic_carbon=self.config.value_avg_soil_organic_carbon_water_equiv,
                    )
                )

            elif self.config.neutron_conversion_method == "koehli_etal_2021":
                n0_opt, abs_error = (
                    self._find_optimal_n0_single_day_koehli_etal_2021(
                        gravimetric_sm_on_day=grav_sm,
                        neutron_mean=neutron_mean,
                        abs_air_humidity=metrics["absolute_air_humidity"],
                        lattice_water=self.config.value_avg_lattice_water,
                        water_equiv_soil_organic_carbon=self.config.value_avg_soil_organic_carbon_water_equiv,
                        koehli_method_form=self.config.koehli_method_form,
                    )
                )

            metrics.update({"optimal_N0": n0_opt, "absolute_error": abs_error})

        return float(
            np.mean(
                [m["optimal_N0"] for m in self.calib_metrics_dict.values()]
            )
        )
