from enum import Enum, auto


class ColumnInfo:
    class Name(Enum):
        DATE_TIME = auto()
        EPI_NEUTRON_COUNT = auto()
        PRESSURE = auto()
        RELATIVE_HUMIDITY = auto()
        INCOMING_NEUTRON_INTENSITY = auto()
        CORRECTED_EPI_NEUTRON_COUNT = auto()
        CORRECTED_EPI_NEUTRON_COUNT_SMOOTH = auto()
        THERM_NEUTRON_COUNT = auto()
        PRECIPITATION = auto()
        SOIL_MOISTURE = auto()
        SOIL_MOISTURE_UNCERTAINTY_UPPER = auto()
        SOIL_MOISTURE_UNCERTAINTY_LOWER = auto()
        SOIL_MOISTURE_MEASURMENT_DEPTH = auto()

        def __str__(self):
            return ColumnInfo._representation[self]

    _representation: dict["ColumnInfo.Name", str] = {
        Name.DATE_TIME: "date_time",
        Name.EPI_NEUTRON_COUNT: "epithermal_neutrons",
        Name.PRESSURE: "air_pressure",
        Name.RELATIVE_HUMIDITY: "air_relative_humidity",
        Name.INCOMING_NEUTRON_INTENSITY: "incoming_neutron_intensity",
        Name.CORRECTED_EPI_NEUTRON_COUNT: "corrected_epithermal_neutrons",
        Name.CORRECTED_EPI_NEUTRON_COUNT_SMOOTH: "corrected_epithermal_neutrons_smooth",
        Name.THERM_NEUTRON_COUNT: "thermal_neutron_count",
        Name.PRECIPITATION: "precipitation",
        Name.SOIL_MOISTURE: "soil_moisture",
        Name.SOIL_MOISTURE_UNCERTAINTY_UPPER: "soil_moisture_uncertainty_upper",
        Name.SOIL_MOISTURE_UNCERTAINTY_LOWER: "soil_moisture_uncertainty_lower",
        Name.SOIL_MOISTURE_MEASURMENT_DEPTH: "crns_measurement_depth",
    }

    @classmethod
    def relabel(cls, column_name: Name, new_label: str):
        cls._representation[column_name] = new_label
