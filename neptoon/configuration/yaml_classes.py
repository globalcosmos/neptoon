"""
This module contains pydantic tables used for validation when importing
YAML data
"""

from pydantic import BaseModel
from typing import Optional, Union
import datetime

################
# Station YAML #
################


class GeneralSiteMetadata(BaseModel):
    site_name: str
    site_country: str
    site_identifier: str
    install_date: Union[str, datetime.date]
    elevation: int
    latitude: float
    longitude: float
    time_zone: Union[str, int]
    cutoff_rigidity: float
    avg_lattice_water: float
    avg_soil_organic_carbon: float
    avg_dry_soil_bulk_density: float
    N0: Optional[float] = None
    beta_coefficient: Optional[float] = None
    reference_pressure: Optional[float] = None
    avg_precipitation: Optional[float] = None
    avg_soil_moisture: Optional[float] = None


class CRNSSensorInformation(BaseModel):
    sensor_tube_type: str
    sensor_height: int
    multiple_tubes: bool


class TimeseriesDataFormat(BaseModel):
    data_format: Union[str, datetime.date]
    resolution: str


class TimeseriesDataFormat_ColumnNames(BaseModel):
    neutron_counts: str
    pressure: str
    relative_humidity: str
    atmospheric_temperature: str
    resolution_column: str
    resolution_default: str
    incoming_neutron_intensity: str


class CalibrationDataFormat(BaseModel):
    format: str


class CalibrationDataFormat_ColumnNames(BaseModel):
    profile: str
    sample_depth: str
    radial_distance_from_sensor: str


class PDFConfiguration(BaseModel):
    title: str
    subtitle: str
    contact: str
    contact_email: str
    cover_image: str


class DataStorage(BaseModel):
    data_source: str
    local_storage_path: str
    local_storage_prefix: str
    local_storage_suffix: str
    cache_data_pickle_store: Optional[str]
    cache_data_restore_pickle: Optional[str]
    FTP_server_host: str
    FTP_server_username: str
    FTP_server_password: str
    FTP_server_data_prefix: str
    FTP_server_data_suffix: str
    remote_folder_SD_path: Optional[str]
    remote_folder_SD_prefix: Optional[str]
    remote_folder_SD_suffix: Optional[str]


class SoilGridsMetadata(BaseModel):
    desired_depth: int
    desired_radius: int
    bulk_density: Optional[float]
    bulk_density_uncertainty: Optional[float]
    soil_organic_carbon: Optional[float]
    soil_organic_carbon_uncertainty: Optional[float]
    ph_of_water: Optional[float]
    ph_of_water_uncertainty: Optional[float]
    cation_exchange_capacity: Optional[float]
    cation_exchange_capacity_uncertainty: Optional[float]
    coarse_fragments_cfvo: Optional[float]
    coarse_fragments_cfvo_uncertainty: Optional[float]
    nitrogen: Optional[float]
    nitrogen_uncertainty: Optional[float]
    sand: Optional[float]
    sand_uncertainty: Optional[float]
    silt: Optional[float]
    silt_uncertainty: Optional[float]
    clay: Optional[float]
    clay_uncertainty: Optional[float]


###################
# Processing YAML #
###################


class MethodSignifier(BaseModel):
    method_name: str


class ReferenceNeutronMonitor(BaseModel):
    NM_auto_download: bool
    NM_path: Optional[str]
    NM_station: str
    NM_resolution: str


class IncomingRadiation(BaseModel):
    new_incoming_column: str
    incoming_method: str
    incoming_ref: int


class AirPressure(BaseModel):
    pressure_method: str
    Dunai_inclination: Optional[float] = None


class AirHumidity(BaseModel):
    absolute_humidity_column_name: str
    humidity_method: str
    alpha: float
    humidity_ref: int


class InvalidData(BaseModel):
    invalid_data: str
    interpolate_neutrons: bool
    interpolate_neutrons_gapsize: Optional[int] = None
    interpolate_coords: bool


class Interpolation(BaseModel):
    interpolate_neutrons: bool
    interpolate_neutrons_gapsize: int


class TemporalAggregation(BaseModel):
    aggregate: str
    aggregate_func: str
    aggregate_minor_vis: str
