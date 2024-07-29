from enum import Enum, auto
import copy


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
        DATE_TIME = auto()
        EPI_NEUTRON_COUNT = auto()
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
        CORRECTED_EPI_NEUTRON_COUNT = auto()
        CORRECTED_EPI_NEUTRON_COUNT_SMOOTH = auto()
        THERM_NEUTRON_COUNT = auto()
        PRECIPITATION = auto()
        SOIL_MOISTURE = auto()
        SOIL_MOISTURE_FINAL = auto()
        SOIL_MOISTURE_UNCERTAINTY_UPPER = auto()
        SOIL_MOISTURE_UNCERTAINTY_LOWER = auto()
        SOIL_MOISTURE_MEASURMENT_DEPTH = auto()
        SOIL_MOISTURE_MEASUREMENT_RADIUS = auto()

        def __str__(self):
            return ColumnInfo._current_representation[self]

    _default_representation: dict["ColumnInfo.Name", str] = {
        Name.DATE_TIME: "date_time",
        Name.EPI_NEUTRON_COUNT: "epithermal_neutrons",
        Name.EPI_NEUTRON_COUNT_FINAL: "epithermal_neutrons_final",
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
        Name.CORRECTED_EPI_NEUTRON_COUNT: "corrected_epithermal_neutrons",
        Name.CORRECTED_EPI_NEUTRON_COUNT_SMOOTH: "corrected_epithermal_neutrons_smooth",
        Name.THERM_NEUTRON_COUNT: "thermal_neutron_count",
        Name.PRECIPITATION: "precipitation",
        Name.SOIL_MOISTURE: "soil_moisture",
        Name.SOIL_MOISTURE_FINAL: "soil_moisture",  # updated to processed soil moisture
        Name.SOIL_MOISTURE_UNCERTAINTY_UPPER: "soil_moisture_uncertainty_upper",
        Name.SOIL_MOISTURE_UNCERTAINTY_LOWER: "soil_moisture_uncertainty_lower",
        Name.SOIL_MOISTURE_MEASURMENT_DEPTH: "crns_measurement_depth",
        Name.SOIL_MOISTURE_MEASUREMENT_RADIUS: "crns_measurement_radius",
    }

    _current_representation = copy.deepcopy(_default_representation)

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
