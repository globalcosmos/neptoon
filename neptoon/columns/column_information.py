from enum import Enum, auto
import copy
from neptoon.logging import get_logger

core_logger = get_logger()


class ColumnInfo:
    """
    Used for storing information related to the cols in CRNS time series
    data. The names of columns are stored here providing a clean area to
    update column names and have this applied across the code base.

    TODO: Ideas for improvements:
        - Add information on whether a col is 'supplied' or 'calculated'
        - Use this information to organise order of 'calculated' columns
    """

    class Name(Enum):
        """
        All of the columns that neptoon could use during any of its
        methods. It provides a place to store relevant information about
        columns. A key aspect is it allows a user to change the expected
        column names during processing without needing to change the
        codebase. By storing as an Enum IDEs can offer autofill when
        typing ColumnInfo.Name....

        The user calls it by requesting the
        string representation of a column name:

        Example
        --------

        >>> crns_data_frame[str(ColumnInfo.Name.SOIL_MOISTURE)] = 1

        """

        DATE_TIME = auto()
        EPI_NEUTRON_COUNT_RAW = auto()
        EPI_NEUTRON_COUNT_CPH = auto()
        EPI_NEUTRON_COUNT_FINAL = auto()
        AIR_PRESSURE = auto()
        AIR_RELATIVE_HUMIDITY = auto()
        AIR_TEMPERATURE = auto()
        INCOMING_NEUTRON_INTENSITY = auto()
        SATURATION_VAPOUR_PRESSURE = auto()
        ACTUAL_VAPOUR_PRESSURE = auto()
        ABSOLUTE_HUMIDITY = auto()
        HUMIDITY_CORRECTION = auto()
        INTENSITY_CORRECTION = auto()
        PRESSURE_CORRECTION = auto()
        ABOVEGROUND_BIOMASS_CORRECTION = auto()
        CORRECTED_EPI_NEUTRON_COUNT = auto()
        CORRECTED_EPI_NEUTRON_COUNT_FINAL = auto()
        CORRECTED_EPI_NEUTRON_COUNT_UNCERTAINTY = auto()
        CORRECTED_EPI_NEUTRON_COUNT_UPPER_COUNT = auto()
        CORRECTED_EPI_NEUTRON_COUNT_LOWER_COUNT = auto()
        THERM_NEUTRON_COUNT_RAW = auto()
        THERM_NEUTRON_COUNT_CPH = auto()
        PRECIPITATION = auto()
        SOIL_MOISTURE_GRAV = auto()
        SOIL_MOISTURE_VOL = auto()
        SOIL_MOISTURE_VOL_FINAL = auto()
        SOIL_MOISTURE_UNCERTAINTY_VOL_UPPER = auto()
        SOIL_MOISTURE_UNCERTAINTY_VOL_LOWER = auto()
        SOIL_MOISTURE_MEASURMENT_DEPTH = auto()
        SOIL_MOISTURE_MEASUREMENT_RADIUS = auto()
        LATITUDE = auto()
        LONGITUDE = auto()
        ELEVATION = auto()
        REFERENCE_INCOMING_NEUTRON_VALUE = auto()
        SITE_CUTOFF_RIGIDITY = auto()
        REFERENCE_MONITOR_CUTOFF_RIGIDITY = auto()
        NMDB_REFERENCE_STATION = auto()
        RC_CORRECTION_FACTOR = auto()
        DRY_SOIL_BULK_DENSITY = auto()
        LATTICE_WATER = auto()
        SOIL_ORGANIC_CARBON = auto()
        MEAN_PRESSURE = auto()
        SITE_BIOMASS = auto()
        N0 = auto()
        BETA_COEFFICIENT = auto()
        CALIB_DEPTH_OF_SAMPLE = auto()
        CALIB_DISTANCE_TO_SENSOR = auto()
        CALIB_BULK_DENSITY = auto()
        CALIB_PROFILE_ID = auto()
        CALIB_SOIL_MOISTURE_GRAVIMETRIC = auto()
        CALIB_SOIL_ORGANIC_CARBON = auto()
        CALIB_LATTICE_WATER = auto()

        def __str__(self):
            return ColumnInfo._current_representation[self]

    _default_representation: dict["ColumnInfo.Name", str] = {
        Name.DATE_TIME: "date_time",
        Name.EPI_NEUTRON_COUNT_RAW: "epithermal_neutrons_raw",
        Name.EPI_NEUTRON_COUNT_CPH: "epithermal_neutrons_cph",
        Name.EPI_NEUTRON_COUNT_FINAL: "epithermal_neutrons_cph",
        Name.AIR_PRESSURE: "air_pressure",
        Name.AIR_RELATIVE_HUMIDITY: "air_relative_humidity",
        Name.AIR_TEMPERATURE: "air_temperature",
        Name.INCOMING_NEUTRON_INTENSITY: "incoming_neutron_intensity",
        Name.SATURATION_VAPOUR_PRESSURE: "saturation_vapour_pressure",
        Name.ACTUAL_VAPOUR_PRESSURE: "actual_vapour_pressure",
        Name.ABSOLUTE_HUMIDITY: "absolute_humidity",
        Name.HUMIDITY_CORRECTION: "humidity_correction",
        Name.INTENSITY_CORRECTION: "incoming_neutron_intensity_correction",
        Name.PRESSURE_CORRECTION: "atmospheric_pressure_correction",
        Name.ABOVEGROUND_BIOMASS_CORRECTION: "aboveground_biomass_correction",
        Name.CORRECTED_EPI_NEUTRON_COUNT: "corrected_epithermal_neutrons",
        Name.CORRECTED_EPI_NEUTRON_COUNT_FINAL: "corrected_epithermal_neutrons",
        Name.CORRECTED_EPI_NEUTRON_COUNT_UNCERTAINTY: "corrected_epithermal_neutrons_uncertainty",
        Name.CORRECTED_EPI_NEUTRON_COUNT_UPPER_COUNT: "corrected_epithermal_neutrons_upper_count",
        Name.CORRECTED_EPI_NEUTRON_COUNT_LOWER_COUNT: "corrected_epithermal_neutrons_lower_count",
        Name.THERM_NEUTRON_COUNT_RAW: "thermal_neutron_count_raw",
        Name.THERM_NEUTRON_COUNT_CPH: "thermal_neutron_count_cph",
        Name.PRECIPITATION: "precipitation",
        Name.SOIL_MOISTURE_GRAV: "soil_moisture_gravimetric",
        Name.SOIL_MOISTURE_VOL: "soil_moisture_volumetric",
        Name.SOIL_MOISTURE_VOL_FINAL: "soil_moisture_volumetric",  # updated to processed soil moisture
        Name.SOIL_MOISTURE_UNCERTAINTY_VOL_UPPER: "soil_moisture_vol_uncertainty_upper",
        Name.SOIL_MOISTURE_UNCERTAINTY_VOL_LOWER: "soil_moisture_vol_uncertainty_lower",
        Name.SOIL_MOISTURE_MEASURMENT_DEPTH: "crns_measurement_depth_cm",
        Name.SOIL_MOISTURE_MEASUREMENT_RADIUS: "crns_measurement_radius_m",
        Name.LATITUDE: "latitude",
        Name.LONGITUDE: "longitude",
        Name.ELEVATION: "elevation",
        Name.REFERENCE_INCOMING_NEUTRON_VALUE: "reference_incoming_neutron_value",
        Name.SITE_CUTOFF_RIGIDITY: "site_cutoff_rigidity",
        Name.REFERENCE_MONITOR_CUTOFF_RIGIDITY: "reference_monitor_cutoff_rigidity",
        Name.NMDB_REFERENCE_STATION: "nmdb_reference_station",
        Name.RC_CORRECTION_FACTOR: "rc_correction_factor",
        Name.DRY_SOIL_BULK_DENSITY: "dry_soil_bulk_density",
        Name.LATTICE_WATER: "lattice_water",
        Name.SOIL_ORGANIC_CARBON: "soil_organic_carbon",
        Name.MEAN_PRESSURE: "mean_pressure",
        Name.SITE_BIOMASS: "site_biomass",
        Name.N0: "n0",
        Name.BETA_COEFFICIENT: "beta_coefficient",
        Name.CALIB_DEPTH_OF_SAMPLE: "depth_of_sample",
        Name.CALIB_DISTANCE_TO_SENSOR: "distance_to_sensor",
        Name.CALIB_BULK_DENSITY: "bulk_density",
        Name.CALIB_PROFILE_ID: "profile_id",
        Name.CALIB_SOIL_MOISTURE_GRAVIMETRIC: "soil_moisture_gravimetric",
        Name.CALIB_SOIL_ORGANIC_CARBON: "soil_organic_carbon",
        Name.CALIB_LATTICE_WATER: "lattice_water",
    }

    _current_representation = copy.deepcopy(_default_representation)

    """
    SITE_INFO_TO_COLUMN_INFO is a mapping dictionary used when adding
    columns to the crns_data_frame using the SiteInformation class.

    See CRNSDataHub.prepare_static_values() for context.
    """
    SITE_INFO_TO_COLUMN_INFO = {
        "latitude": Name.LATITUDE,
        "longitude": Name.LONGITUDE,
        "elevation": Name.ELEVATION,
        "reference_incoming_neutron_value": Name.REFERENCE_INCOMING_NEUTRON_VALUE,
        "dry_soil_bulk_density": Name.DRY_SOIL_BULK_DENSITY,
        "lattice_water": Name.LATTICE_WATER,
        "soil_organic_carbon": Name.SOIL_ORGANIC_CARBON,
        "site_cutoff_rigidity": Name.SITE_CUTOFF_RIGIDITY,
        "mean_pressure": Name.MEAN_PRESSURE,
        "site_biomass": Name.SITE_BIOMASS,
        "n0": Name.N0,
        "beta_coefficient": Name.BETA_COEFFICIENT,
        "reference_monitor_cutoff_rigidity": Name.REFERENCE_MONITOR_CUTOFF_RIGIDITY,
    }

    @classmethod
    def relabel(cls, column_name: Name, new_label: str):
        """
        Class method which allows a user to change the expected string
        of a column type.

        Parameters
        ----------
        column_name : Name
            The Name of the column e.g., Name.EPI_NEUTRON_COUNT
        new_label : str
            A string that represents the new column name to expect
            throughout processing.
        """
        cls._current_representation[column_name] = new_label

    @classmethod
    def reset_labels(cls):
        """
        Class method to reset all the labels to default values supplied
        in neptoon.
        """
        cls._current_representation = copy.deepcopy(
            cls._default_representation
        )

    @classmethod
    def get_col_name(cls, column_name: str):
        """
        Method to return the string representation of the name of a
        Column

        Parameters
        ----------
        column_name : str
            The enum object from which the name is required

        Returns
        -------
        str
            The string representation of the name.
        """
        return str(getattr(cls.Name, column_name.upper()))
