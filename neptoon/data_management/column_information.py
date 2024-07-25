from enum import Enum, auto
import copy
from neptoon.logging import get_logger

core_logger = get_logger()


class ColumnInfo:  # TODO Change to Columns
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
        EPI_NEUTRON_COUNT = auto()
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
        SOIL_MOISTURE_UNCERTAINTY_UPPER = auto()
        SOIL_MOISTURE_UNCERTAINTY_LOWER = auto()
        SOIL_MOISTURE_MEASURMENT_DEPTH = auto()
        SOIL_MOISTURE_MEASUREMENT_RADIUS = auto()
        LATITUDE = auto()
        LONGITUDE = auto()
        ELEVATION = auto()
        REFERENCE_INCOMING_NEUTRON_VALUE = auto()
        DRY_SOIL_BULK_DENSITY = auto()
        LATTICE_WATER = auto()
        SOIL_ORGANIC_CARBON = auto()
        CUTOFF_RIGIDITY = auto()
        MEAN_PRESSURE = auto()
        SITE_BIOMASS = auto()
        N0 = auto()
        BETA_COEFFICIENT = auto()
        L_COEFFICIENT = auto()

        def __str__(self):
            return ColumnInfo._current_representation[self]

    _default_representation: dict["ColumnInfo.Name", str] = {
        Name.DATE_TIME: "date_time",
        Name.EPI_NEUTRON_COUNT: "epithermal_neutrons",
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
        Name.SOIL_MOISTURE_UNCERTAINTY_UPPER: "soil_moisture_uncertainty_upper",
        Name.SOIL_MOISTURE_UNCERTAINTY_LOWER: "soil_moisture_uncertainty_lower",
        Name.SOIL_MOISTURE_MEASURMENT_DEPTH: "crns_measurement_depth",
        Name.SOIL_MOISTURE_MEASUREMENT_RADIUS: "crns_measurement_radius",
        Name.LATITUDE: "latitude",
        Name.LONGITUDE: "longitude",
        Name.ELEVATION: "elevation",
        Name.REFERENCE_INCOMING_NEUTRON_VALUE: "reference_incoming_neutron_value",
        Name.DRY_SOIL_BULK_DENSITY: "dry_soil_bulk_density",
        Name.LATTICE_WATER: "lattice_water",
        Name.SOIL_ORGANIC_CARBON: "soil_organic_carbon",
        Name.CUTOFF_RIGIDITY: "cutoff_rigidity",
        Name.MEAN_PRESSURE: "mean_pressure",
        Name.SITE_BIOMASS: "site_biomass",
        Name.N0: "n0",
        Name.BETA_COEFFICIENT: "beta_coefficient",
        Name.L_COEFFICIENT: "l_coefficient",
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
        "cutoff_rigidity": Name.CUTOFF_RIGIDITY,
        "mean_pressure": Name.MEAN_PRESSURE,
        "site_biomass": Name.SITE_BIOMASS,
        "n0": Name.N0,
        "beta_coefficient": Name.BETA_COEFFICIENT,
        "l_coefficient": Name.L_COEFFICIENT,
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
    def add_custom_name(cls, name: str):
        if not hasattr(cls.Name, name.upper()):
            cls.Name = Enum(
                "Name",
                {
                    **{
                        enum_member.name: enum_member.value
                        for enum_member in cls.Name
                    },
                    name.upper(): auto(),
                },
            )
        cls._current_representation[getattr(cls.Name, name.upper())] = (
            name.lower()
        )
        cls.SITE_INFO_TO_COLUMN_INFO[name.lower()] = getattr(
            cls.Name, name.upper()
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
