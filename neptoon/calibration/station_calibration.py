import pandas as pd
import numpy as np
import copy
from datetime import timedelta

# from scipy.optimize import minimize
from neptoon.columns import ColumnInfo
from neptoon.corrections import Schroen2017, neutrons_to_grav_sm_desilets
from neptoon.data_prep.conversions import AbsoluteHumidityCreator


class CalibrationConfiguration:
    """
    Configuration class for calibration steps
    """

    def __init__(
        self,
        hours_of_data_around_calib: int = 6,
        converge_accuracy: float = 0.01,
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
        abs_air_humidity_column_name: str = str(
            ColumnInfo.Name.ABSOLUTE_HUMIDITY
        ),
        neutron_column_name: str = str(
            ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL
        ),
        air_pressure_column_name: str = str(ColumnInfo.Name.AIR_PRESSURE),
    ):
        """
        Attributes.

        Parameters
        ----------
        date_time_column_name : str, optional
            The name of the column with date time information, by
            default str(ColumnInfo.Name.DATE_TIME)
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
        abs_air_humidity_column_name : str, optional
            Name of the column with absolute air humidity values (g/cm3), by default
            str(ColumnInfo.Name.ABSOLUTE_HUMIDITY)
        neutron_column_name : str, optional
            Name of the column with corrected neutrons in it, by default
            str(ColumnInfo.Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL)
        air_pressure_column_name : str, optional
            Name of the column with air pressure vlaues in it, by
            default str(ColumnInfo.Name.AIR_PRESSURE)
        """
        self.hours_of_data_around_calib = hours_of_data_around_calib
        self.converge_accuracy = converge_accuracy
        self.calib_data_date_time_column_name = (
            calib_data_date_time_column_name
        )
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
        self.abs_air_humidity_column_name = abs_air_humidity_column_name
        self.neutron_column_name = neutron_column_name
        self.air_pressure_column_name = air_pressure_column_name


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

    __slots__ = [
        # Input
        "pid",  # arbitrary profile id
        "soil_moisture_gravimetric",  # soil moisture values in g/g
        "sm_total_grv",  # soil moisture values in g/g
        "sm_total_vol",  # soil moisture values in g/g
        "depth",  # depth values in cm
        "bulk_density",  # bulk density
        "bulk_density_mean",
        "site_avg_bulk_density",
        "_distance",  # distance from the CRNS in m
        "lattice_water",  # lattice water in g/g
        "site_avg_lattice_water",
        "soil_organic_carbon",  # soil organic carbon in g/g
        "site_avg_organic_carbon",
        "calibration_day",  # the calibration day for the sample - datetime
        # Calculated
        "D86",  # penetration depth
        "horizontal_weight",  # radial weight of this profile
        "sm_total_weighted_avg_vol",  # vertically weighted average sm
        "sm_total_weighted_avg_grv",  # vertically weighted average sm
        "vertical_weights",
        "rescaled_distance",
        "data",  # DataFrame
    ]

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
        # self.bulk_density_mean = np.array(bulk_density).mean()
        self.site_avg_bulk_density = site_avg_bulk_density
        self.calibration_day = calibration_day
        self.soil_organic_carbon = (
            np.array(soil_organic_carbon)
            if soil_organic_carbon is None
            else np.zeros_like(soil_moisture_gravimetric)
        )
        self.site_avg_organic_carbon = site_avg_organic_carbon
        self.lattice_water = self.lattice_water = (
            np.array(lattice_water)
            if lattice_water is not None
            else np.zeros_like(soil_moisture_gravimetric)
        )
        self.site_avg_lattice_water = site_avg_lattice_water
        self.vertical_weights = np.ones_like(soil_moisture_gravimetric)
        self._calculate_sm_total_vol()
        self._calculate_sm_total_grv()

        # Scalar values
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
        sm_total_vol = (
            self.soil_moisture_gravimetric
            + self.site_avg_lattice_water
            + self.site_avg_organic_carbon * 0.555
        ) * self.site_avg_bulk_density
        self.sm_total_vol = sm_total_vol

    def _calculate_sm_total_grv(self):
        """
        Calculate total gravimetric soil moisture.
        """
        sm_total_grv = (
            self.soil_moisture_gravimetric
            + self.site_avg_lattice_water
            + self.site_avg_organic_carbon * 0.555
        )
        self.sm_total_grv = sm_total_grv


class PrepareCalibrationData:
    """
    Prepares the calibration dataframe
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

    def prepare_calibration_data(self):
        """
        Prepares the calibration data into a list of profiles.
        """
        site_avg_bulk_density = self.calibration_data_frame[
            self.config.bulk_density_of_sample_column
        ].mean()

        site_avg_lattice_water = self.calibration_data_frame[
            self.config.lattice_water_column
        ].mean()

        site_avg_organic_carbon = self.calibration_data_frame[
            self.config.soil_organic_carbon_column
        ].mean()

        if np.isnan(site_avg_lattice_water):
            site_avg_lattice_water = 0

        if np.isnan(site_avg_organic_carbon):
            site_avg_organic_carbon = 0

        self._create_list_of_df()

        for data_frame in self.list_of_data_frames:
            calibration_day_profiles = self._create_calibration_day_profiles(
                single_day_data_frame=data_frame,
                site_avg_bulk_density=site_avg_bulk_density,
                site_avg_organic_carbon=site_avg_organic_carbon,
                site_avg_lattice_water=site_avg_lattice_water,
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

        self.output_dictionary = {}

    def _get_time_series_data_for_day(
        self,
        day,
    ):
        return self.time_series_data_object.data_dict[day]

    def apply_weighting_to_multiple_days(self):

        for day in self.calib_data_object.unique_calibration_days:

            tmp_data = self._get_time_series_data_for_day(day)
            day_list_of_profiles = [
                profile
                for profile in self.calib_data_object.list_of_profiles
                if profile.calibration_day == day
            ]

            # Get initial average SM
            sm_total_vol_values = [
                np.array(profile.sm_total_vol).flatten()
                for profile in day_list_of_profiles
                if profile.sm_total_vol is not None
            ]
            flattened = np.concatenate(sm_total_vol_values)
            valid_values = flattened[~np.isnan(flattened)]
            sm_estimate = np.mean(valid_values)

            # Get average air humidity and air pressure
            average_air_humidity = tmp_data[
                self.config.abs_air_humidity_column_name
            ].mean()
            average_air_pressure = tmp_data[
                self.config.air_pressure_column_name
            ].mean()

            field_average_sm_vol, field_average_sm_grav, footprint = (
                self.calculate_weighted_sm_average(
                    day_list_of_profiles=day_list_of_profiles,
                    initial_sm_estimate=sm_estimate,
                    average_air_humidity=average_air_humidity,
                    average_air_pressure=average_air_pressure,
                )
            )

            info_dictionary = {
                "field_average_soil_moisture_volumetric": field_average_sm_vol,
                "field_average_soil_moisture_gravimetric": field_average_sm_grav,
                "horizontal_footprint_radius_in_meters": footprint,
            }

            self.output_dictionary[day] = info_dictionary

    def calculate_weighted_sm_average(
        self,
        day_list_of_profiles,
        initial_sm_estimate: float,
        average_air_humidity: float,
        average_air_pressure: float,
    ):
        """_summary_

        Parameters
        ----------
        day_list_of_profiles : _type_
            List of profiles for the calibration day being processed
        initial_sm_estimate : float
            Initial soil moisture estimate (usually equal average)
        average_air_humidity : float
            Average absolute air humidity
        average_air_pressure : float
            Air pressure average during calibration period (hPa)

        Returns
        -------
        _type_
            _description_
        """

        sm_estimate = copy.deepcopy(initial_sm_estimate)
        accuracy = 1
        field_average_sm_volumetric = None
        field_average_sm_gravimetric = None

        while accuracy > self.config.converge_accuracy:
            profile_sm_averages_volumetric = []
            profile_sm_averages_gravimetric = []
            profiles_horizontal_weights = []

            for profile in day_list_of_profiles:

                profile.rescaled_distance = Schroen2017.rescale_distance(
                    distance=profile.rescaled_distance,
                    pressure=average_air_pressure,
                    soil_moisture=sm_estimate,
                )

                profile.D86 = Schroen2017.calculate_measurement_depth(
                    distance=profile.rescaled_distance,
                    bulk_density=profile.site_avg_bulk_density,
                    soil_moisture=sm_estimate,
                )

                profile.vertical_weights = Schroen2017.vertical_weighting(
                    profile.depth,
                    bulk_density=profile.site_avg_bulk_density,
                    soil_moisture=sm_estimate,
                )

                # Calculate weighted sm average
                profile.sm_total_weighted_avg_vol = np.average(
                    profile.sm_total_vol, weights=profile.vertical_weights
                )
                profile.sm_total_weighted_avg_grv = np.average(
                    profile.sm_total_grv, weights=profile.vertical_weights
                )

                profile.horizontal_weight = Schroen2017.horizontal_weighting(
                    distance=profile.rescaled_distance,
                    soil_moisture=profile.sm_total_weighted_avg_vol,
                    air_humidity=average_air_humidity,
                )

                # create a list of average sm and horizontal weights
                profile_sm_averages_volumetric.append(
                    profile.sm_total_weighted_avg_vol
                )
                profile_sm_averages_gravimetric.append(
                    profile.sm_total_weighted_avg_grv
                )
                profiles_horizontal_weights.append(profile.horizontal_weight)

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
                (field_average_sm_volumetric - sm_estimate) / sm_estimate
            )
            if accuracy > self.config.converge_accuracy:

                sm_estimate = copy.deepcopy(field_average_sm_volumetric)
                profile_sm_averages_volumetric = []
                profile_sm_averages_gravimetric = []
                profiles_horizontal_weights = []

        footprint_m = Schroen2017.calculate_footprint_radius(
            soil_moisture=field_average_sm_volumetric,
            air_humidity=average_air_humidity,
            pressure=average_air_pressure,
        )

        return (
            field_average_sm_volumetric,
            field_average_sm_gravimetric,
            footprint_m,
        )

    def return_output_dict_as_dataframe(self):
        df = pd.DataFrame.from_dict(self.output_dictionary, orient="index")
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

    def find_optimal_N0(
        self,
    ):
        df = self.return_output_dict_as_dataframe()
        for index, row in df.iterrows():
            calib_day = pd.to_datetime(row["calibration_day"])
            calib_data_frame = self.time_series_data_object.data_dict[
                calib_day
            ]
            gravimetric_sm_on_day = row[
                "field_average_soil_moisture_gravimetric"
            ]

            N0_optimal, absolute_error = (
                self.find_optimal_N0_single_day_iteration_style(
                    gravimetric_sm_on_day=gravimetric_sm_on_day,
                    calib_data_frame_subset=calib_data_frame,
                )
            )

            # Update the original dictionary
            self.output_dictionary[calib_day]["optimal_N0"] = N0_optimal
            self.output_dictionary[calib_day][
                "absolute_error"
            ] = absolute_error
        df = self.return_output_dict_as_dataframe()
        average_n0 = df["optimal_N0"].mean()
        return average_n0

    def find_optimal_N0_single_day_iteration_style(
        self,
        gravimetric_sm_on_day,
        calib_data_frame_subset,
    ):
        neutron_mean = calib_data_frame_subset[
            self.config.neutron_column_name
        ].mean()
        n0_range = pd.Series(range(int(neutron_mean), int(neutron_mean * 2.5)))

        def calculate_sm_and_error(n0):
            sm_prediction = neutrons_to_grav_sm_desilets(
                neutrons=neutron_mean, n0=n0
            )
            absolute_error = abs(sm_prediction - gravimetric_sm_on_day)
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

    def find_optimal_N0_single_day_minimise_style(
        self,
        gravimetric_sm_on_day,
        average_neutrons_on_day,
        N0_initial=1000,
        N0_bounds=(400, 4000),
    ):
        """TODO"""
        # result = minimize(
        #     self.find_N0_error_function,
        #     N0_initial,
        #     args=(
        #         gravimetric_sm_on_day,
        #         self.time_series_data_object.corrected_neutron_data_frame[
        #             self.neutron_column_name
        #         ],
        #     ),
        #     bounds=[N0_bounds],
        # )
        # N0_optimal = result.x[0]
        # rmse = result["fun"]
        # return N0_optimal, rmse
        pass
