from enum import Enum, auto


class ColumnInfo:
    class Name(Enum):
        DATE_TIME = auto()
        EPI_NEUTRON_COUNT = auto()
        PRESSURE = auto()
        RELATIVE_HUMIDITY = auto()
        INCOMING_NEUTRON_INTENSITY = auto()
        CORRECTED_EPI_NEUTRON_COUNT = auto()
        THERM_NEUTRON_COUNT = auto()
        PRECIPITATION = auto()

        def __str__(self):
            return ColumnInfo._representation[self]

    _representation: dict["ColumnInfo.Name", str] = {
        Name.DATE_TIME: "date_time",
        Name.EPI_NEUTRON_COUNT: "epithermal_neutrons",
        Name.PRESSURE: "air_pressure",
        Name.RELATIVE_HUMIDITY: "air_relative_humidity",
        Name.INCOMING_NEUTRON_INTENSITY: "incoming_neutron_intensity",
        Name.CORRECTED_EPI_NEUTRON_COUNT: "corrected_epithermal_neutrons",
        Name.THERM_NEUTRON_COUNT: "thermal_neutron_count",
    }

    @classmethod
    def relabel(cls, column_name: Name, new_label: str):
        cls._representation[column_name] = new_label
