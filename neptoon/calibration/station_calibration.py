import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict, List
from neptoon.data_management.column_information import ColumnInfo


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
        "distance",  # distance from the CRNS in m
        "lattice_water",  # lattice water in g/g
        "soil_organic_carbon",  # soil organic carbon in g/g
        "calibration_day",  # the calibration day for the sample - datetime
        # Calculated
        "D86",  # penetration depth
        "w_r",  # radial weight of this profile
        "sm_total_weghted_avg_vol",  # vertically weighted average sm
        "sm_total_weighted_avg_grv",  # vertically weighted average sm
        "data",  # DataFrame
    ]

    def __init__(
        self,
        soil_moisture_gravimetric,
        depth,
        bulk_density,
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
        self.bulk_density_mean = np.array(bulk_density).mean()
        self.calibration_day = calibration_day
        self.soil_organic_carbon = (
            np.array(soil_organic_carbon)
            if soil_organic_carbon is None
            else np.zeros_like(soil_moisture_gravimetric)
        )
        self.lattice_water = self.lattice_water = (
            np.array(lattice_water)
            if lattice_water is not None
            else np.zeros_like(soil_moisture_gravimetric)
        )
        self.data = None
        self.update_data()

        # Scalar values
        self.distance = distance
        self.D86 = np.nan
        self.sm_total_weighted_avg_grv = np.nan
        self.sm_total_weghted_avg_vol = np.nan
        self.w_r = np.nan

    def update_data(self):
        """
        Update the internal DataFrame with current values and perform
        calculations.
        """
        if not self.data:
            self.data = pd.DataFrame()

        self.data["pid"] = self.pid
        self.data["soil_moisture_gravimetric"] = self.soil_moisture_gravimetric
        self.data["depth"] = self.depth
        self.data["bulk_density"] = self.bulk_density
        self.data["lattice_water"] = self.lattice_water
        self.data["soil_organic_carbon"] = self.soil_organic_carbon

        if "weight" not in self.data.columns:
            self.data["weight"] = np.nan

        self._calculate_sm_total_vol()
        self._calculate_sm_total_grv()
        self.data["sm_total_vol"] = self.sm_total_vol
        self.data["sm_total_grv"] = self.sm_total_grv

    def _calculate_sm_total_vol(self):
        """
        Calculate total volumetric soil moisture.
        """
        sm_total_vol = (
            self.data["soil_moisture_gravimetric"]
            + self.data["lattice_water"]
            + self.data["soil_organic_carbon"] * 0.555
        ) * self.data["bulk_density"]
        self.sm_total_vol = sm_total_vol

    def _calculate_sm_total_grv(self):
        """
        Calculate total gravimetric soil moisture.
        """
        sm_total_grv = (
            self.data["soil_moisture_gravimetric"]
            + self.data["lattice_water"]
            + self.data["soil_organic_carbon"] * 0.555
        )
        self.sm_total_grv = sm_total_grv


class PrepareCalibrationData:
    """
    Prepares the calibration dataframe
    """

    def __init__(
        self,
        calibration_data_frame: pd.DataFrame,
        date_time_column_name: str = str(ColumnInfo.Name.DATE_TIME),
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
    ):
        """
        Instantiate attributes

        Parameters
        ----------
        calibration_data_frame : pd.DataFrame
            The dataframe with the calibration sample data in it. If
            multiple calibration days are available these should be
            stacked in the same dataframe.
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
        """

        self.calibration_data_frame = calibration_data_frame
        self.date_time_column_name = date_time_column_name
        self.sample_depth_column = sample_depth_column
        self.distance_column = distance_column
        self.bulk_density_of_sample_column = bulk_density_of_sample_column
        self.profile_id_column = profile_id_column
        self.soil_moisture_gravimetric_column = (
            soil_moisture_gravimetric_column
        )
        self.soil_organic_carbon_column = soil_organic_carbon_column
        self.lattice_water_column = lattice_water_column
        self._ensure_date_time_index()

        self.unique_calibration_days = np.unique(
            self.calibration_data_frame[self.date_time_column_name]
        )
        self.list_of_data_frames = []
        self.list_of_profiles = []

    def _ensure_date_time_index(self):
        """
        Converts the date time column so the values are datetime type.
        """

        self.calibration_data_frame[self.date_time_column_name] = (
            pd.to_datetime(
                self.calibration_data_frame[self.date_time_column_name],
                utc=True,
            )
        )

    def _create_list_of_df(self):
        """
        Splits up the self.calibration_data_frame into individual data
        frames, where each data frame is a different calibration day.
        """

        self.list_of_data_frames = [
            self.calibration_data_frame[
                self.calibration_data_frame[self.date_time_column_name]
                == calibration_day
            ]
            for calibration_day in self.unique_calibration_days
        ]

    def _create_calibration_day_profiles(
        self,
        single_day_data_frame,
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
        profile_ids = np.unique(single_day_data_frame[self.profile_id_column])
        for pid in profile_ids:
            temp_df = single_day_data_frame[
                single_day_data_frame[self.profile_id_column] == pid
            ]
            soil_profile = self._create_individual_profile(
                pid=pid,
                profile_data_frame=temp_df,
            )

            calibration_day_profiles.append(soil_profile)
        return calibration_day_profiles

    def _create_individual_profile(
        self,
        pid,
        profile_data_frame,
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
        distances = profile_data_frame[self.distance_column].median()
        depths = profile_data_frame[self.sample_depth_column]
        bulk_density = profile_data_frame[self.bulk_density_of_sample_column]
        soil_moisture_gravimetric = profile_data_frame[
            self.soil_moisture_gravimetric_column
        ]
        soil_organic_carbon = profile_data_frame[
            self.soil_organic_carbon_column
        ]
        lattice_water = profile_data_frame[self.lattice_water_column]
        calibration_datetime = profile_data_frame[self.date_time_column_name]
        soil_profile = SampleProfile(
            soil_moisture_gravimetric=soil_moisture_gravimetric,
            depth=depths,
            bulk_density=bulk_density,
            distance=distances,
            lattice_water=lattice_water,
            soil_organic_carbon=soil_organic_carbon,
            pid=pid,
            calibration_day=calibration_datetime,
        )
        return soil_profile

    def prepare_calibration_data(self):
        """
        Prepares the calibration data into a list of profiles.
        """

        self._create_list_of_df()

        for data_frame in self.list_of_data_frames:
            calibration_day_profiles = self._create_calibration_day_profiles(
                data_frame
            )
            self.list_of_profiles.append(calibration_day_profiles)


class PrepareNeutronCorrectedData:

    def __init__(
        self,
        corrected_neutron_data_frame: pd.DataFrame,
        calibration_data_prepper: PrepareCalibrationData,
        hours_of_data_around_calib: int = 6,
    ):
        self.corrected_neutron_data_frame = corrected_neutron_data_frame
        self.calibration_data_prepper = calibration_data_prepper
        self.hours_of_data_around_calib = hours_of_data_around_calib
        self.data_dict = {}

        self._ensure_date_time_index()

    def _ensure_date_time_index(self):
        """
        Converts the date time column so the values are datetime type.
        """

        self.corrected_neutron_data_frame.index = pd.to_datetime(
            self.corrected_neutron_data_frame.index,
            utc=True,
        )

    def extract_calibration_day_values(self):
        calibration_indicies_dict = self._extract_calibration_day_indices(
            hours_of_data=self.hours_of_data_around_calib
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
    ):
        self.time_series_data_object = time_series_data_object
        self.calib_data_object = calib_data_object

    def _get_time_series_data_for_day(
        self,
        day,
    ):
        return self.time_series_data_object.data_dict[day]

    def apply_weighting_steps(self):
        for day in self.calib_data_object.unique_calibration_days:
            tmp_data = self._get_time_series_data_for_day(day)
            day_list_of_profiles = [
                profile
                for profile in self.calib_data_object.list_of_profiles
                if profile.calibration_day == day
            ]
            print(day_list_of_profiles)
