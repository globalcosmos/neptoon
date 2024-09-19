# %%
import numpy as np
import pandas
import matplotlib.pyplot as plt
from neptoon.corrections_and_functions.calibration_functions import Schroen2017
from pathlib import Path
from neptoon.calibration.station_calibration import (
    PrepareCalibrationData,
    SampleProfile,
)


# %%
# class Profile:

#     latest_pid = 0

#     __slots__ = [
#         # Input
#         "pid",  # arbitrary profile id
#         "sm",  # soil moisture values in g/g
#         "sm_tot_grv",  # soil moisture values in g/g
#         "sm_tot_vol",  # soil moisture values in g/g
#         "d",  # depth values in cm
#         "bd",  # bulk density
#         "bd_mean",
#         "r",  # distance from the CRNS in m
#         "lw",  # lattice water in g/g
#         "soc",  # soil organic carbon in g/g
#         # Calculated
#         "D86",  # penetration depth
#         "w_r",  # radial weight of this profile
#         "sm_tot_wavg_vol",  # vertically weighted average sm
#         "sm_tot_wavg_grv",  # vertically weighted average sm
#         "data",  # DataFrame
#     ]

#     def __init__(self, sm, d, bd, r=1, lw=0, soc=0, pid=None):

#         # Vector data
#         if pid is None:
#             Profile.latest_pid += 1
#             self.pid = Profile.latest_pid
#         else:
#             self.pid = pid
#         self.sm = np.array(sm)
#         self.d = np.array(d)
#         self.bd = np.array(bd)
#         self.bd_mean = np.array(bd).mean()
#         self.soc = np.array(soc)
#         self.lw = np.array(lw)
#         self.data = None
#         self.update_data()

#         # Scalar values
#         self.r = r
#         self.D86 = np.nan
#         self.sm_tot_wavg_grv = np.nan
#         self.sm_tot_wavg_vol = np.nan
#         self.w_r = np.nan

#     def update_data(self):
#         if not self.data:
#             self.data = pandas.DataFrame()
#         self.data["pid"] = self.pid
#         self.data["sm"] = self.sm
#         self.data["d"] = self.d
#         self.data["bd"] = self.bd
#         self.data["lw"] = self.lw
#         self.data["soc"] = self.soc
#         if not "weight" in self.data.columns:
#             self.data["weight"] = np.nan
#         self.calculate_sm_tot_vol()
#         self.calculate_sm_tot_grv()
#         self.data["sm_tot_vol"] = self.sm_tot_vol
#         self.data["sm_tot_grv"] = self.sm_tot_grv

#     def calculate_sm_tot_vol(self):
#         sm_tot_vol = (
#             self.data["sm"] + self.data["lw"] + self.data["soc"] * 0.555
#         ) * self.data["bd"]
#         self.sm_tot_vol = sm_tot_vol

#     def calculate_sm_tot_grv(self):
#         sm_tot_grv = (
#             self.data["sm"] + self.data["lw"] + self.data["soc"] * 0.555
#         )
#         self.sm_tot_grv = sm_tot_grv


# %%
this_path = Path(__file__).absolute().parent

calibration_data = pandas.read_csv(
    (
        Path.cwd()
        / Path("tests/calibration/mock_data/Sheepdrove2-calibration.csv")
    ),
    skipinitialspace=True,
)


# %%
prepper = PrepareCalibrationData(
    calibration_data_frame=calibration_data,
    date_time_column_name="DateTime_utc",
    distance_column="Distance_to_CRNS_m",
    sample_depth_column="Profile_Depth_cm",
    bulk_density_of_sample_column="DryBulkDensity_g_cm3",
    soil_moisture_gravimetric_column="SoilMoisture_g_g",
    soil_organic_carbon_column="SoilOrganicCarbon_g_g",
    lattice_water_column="LatticeWater_g_g",
    profile_id_column="Profile_ID",
)

prepper.prepare_calibration_data()

# %%
# cdata
# calibration_data["DateTime_utc"] = pandas.to_datetime(
#     calibration_data["DateTime_utc"], utc=True
# )
# calibration_days = np.unique(calibration_data["DateTime_utc"])
# list_of_profiles = []

# for calibration_day in calibration_days:
#     calibration_day_data = calibration_data[
#         calibration_data["DateTime_utc"] == calibration_day
#     ]
#     calibration_day_profiles = []
#     profile_ids = np.unique(calibration_day_data["Profile_ID"])

#     for pid in profile_ids:
#         df = calibration_day_data[calibration_day_data["Profile_ID"] == pid]
#         distances = df["Distance_to_CRNS_m"].median()
#         depths = df["Profile_Depth_cm"]
#         bd = df["DryBulkDensity_g_cm3"]
#         sm_gg = df["SoilMoisture_g_g"]
#         soc_gg = df["SoilOrganicCarbon_g_g"]
#         lw_gg = df["LatticeWater_g_g"]
#         P = Profile(
#             pid=pid,
#             r=distances,
#             d=depths,
#             bd=bd,
#             sm=sm_gg,
#             lw=lw_gg,
#             soc=soc_gg,
#         )
#         calibration_day_profiles.append(P)
#     list_of_profiles.append(calibration_day_profiles)

# %%
CRNS_data = pandas.read_csv(
    "c:/Users/schroen/Projects/Neptoon/neptoon/tests/calibration/mock_data/Sheepdrove2-CRNS.csv",
    index_col=0,
    parse_dates=True,
)
# %%
indices = CRNS_data.index.get_indexer(list(calibration_days), method="nearest")
# %%
df = pandas.DataFrame()
df["calibration_day"] = calibration_days
df["profiles"] = list_of_profiles
df["sm_tot_wavg_vol"] = np.nan
df["sm_tot_wavg_grv"] = np.nan
df["bd"] = np.nan
df["footprint_depth"] = np.nan
df["footprint_radius"] = np.nan
df["air_pressure"] = 993  # to be taken from CRNS dataset
df["air_humidity"] = CRNS_data.iloc[indices][
    "AirHumidity_gapfilled"
].values  # to be taken from CRNS dataset or DataHub Object
df["neutrons"] = CRNS_data.iloc[indices][
    "NeutronCount_Epithermal_MovAvg24h_corrected"
].values
df
# %%
for index, row in df.iterrows():
    i = 0
    calibration_day = row["calibration_day"]
    print("Calibration day %s" % calibration_day.strftime("%Y-%m-%d %H:%M"))
    for P in row["profiles"]:

        i += 1

        # Calculate volumetric SM from sm_gg, lw, soc, bd
        # P.calculate_sm_vol()
        # First order estimate of the average soil moisture
        sm_estimate = P.sm_tot_vol.mean()

        # Neutron penetration depth at this location
        P.D86 = w = Schroen2017.calculate_measurement_depth(
            distance=P.r, bulk_density=P.bd.mean(), soil_moisture=sm_estimate
        )

        # Weights for this profile
        # data = P.data.copy()
        P.data["weight"] = Schroen2017.vertical_weighting(
            P.data["d"], bulk_density=P.bd.mean(), soil_moisture=sm_estimate
        )
        # Calculate weighted sm average
        P.sm_tot_wavg_vol = np.average(
            P.data["sm_tot_vol"], weights=P.data["weight"]
        )
        P.sm_tot_wavg_grv = np.average(
            P.data["sm_tot_grv"], weights=P.data["weight"]
        )

        # Calculate horizontal weight for this profile
        P.w_r = Schroen2017.horizontal_weighting(
            distance=P.r,
            soil_moisture=P.sm_tot_wavg_vol,
            air_humidity=row["air_humidity"],
        )

        print(
            "  Profile %.0f: vertical wt. avg. SM: %.3f, CRNS depth: %3.0f cm, distance: %2.0f m, horizontal weight: %7.0f"
            % (i, P.sm_tot_wavg_vol, P.D86, P.r, P.w_r)
        )

    # Horizontal average
    profiles_sm_tot_wavg_vol = [P.sm_tot_wavg_vol for P in row["profiles"]]
    profiles_sm_tot_wavg_grv = [P.sm_tot_wavg_grv for P in row["profiles"]]
    # if index == 0:
    #     print(profiles_sm_wavg)
    profiles_weights = [P.w_r for P in row["profiles"]]
    profiles_weights_without_nans = np.ma.MaskedArray(
        profiles_weights, mask=np.isnan(profiles_weights)
    )
    profiles_sm_tot_wavg_vol_without_nans = np.ma.MaskedArray(
        profiles_sm_tot_wavg_vol, mask=np.isnan(profiles_sm_tot_wavg_vol)
    )
    sm_tot_wavg_vol = np.average(
        profiles_sm_tot_wavg_vol_without_nans,
        weights=profiles_weights_without_nans,
    )
    profiles_sm_tot_wavg_grv_without_nans = np.ma.MaskedArray(
        profiles_sm_tot_wavg_grv, mask=np.isnan(profiles_sm_tot_wavg_grv)
    )
    sm_tot_wavg_grv = np.average(
        profiles_sm_tot_wavg_grv_without_nans,
        weights=profiles_weights_without_nans,
    )
    # print("Horizontal wt. avg. SM: %.3f" % sm_wavg)

    df.loc[df["calibration_day"] == calibration_day, "sm_tot_wavg_vol"] = (
        sm_tot_wavg_vol
    )
    df.loc[df["calibration_day"] == calibration_day, "sm_tot_wavg_grv"] = (
        sm_tot_wavg_grv
    )

    # Footprint
    footprint_m = Schroen2017.calculate_footprint_radius(
        soil_moisture=sm_tot_wavg_vol,
        air_humidity=row["air_humidity"],
        pressure=row["air_pressure"],
    )
    print("Footprint radius: %.0f m" % footprint_m)

    df.loc[df["calibration_day"] == calibration_day, "footprint_radius"] = (
        footprint_m
    )

    D86s = [P.D86 for P in row["profiles"]]
    D86s_without_nans = np.ma.MaskedArray(D86s, mask=np.isnan(D86s))
    df.loc[df["calibration_day"] == calibration_day, "footprint_depth"] = (
        np.average(D86s_without_nans)
    )

    bds = [P.bd_mean for P in row["profiles"]]
    bds_without_nans = np.ma.MaskedArray(bds, mask=np.isnan(bds))
    df.loc[df["calibration_day"] == calibration_day, "bd"] = np.average(
        bds_without_nans
    )

# %%
df
# %%
# Plot vertical profiles
for index, row in df.iterrows():
    plt.title("SM profiles, vertical wt. avg. SM, and CRNS depth")
    for P in row["profiles"]:
        plt.plot(P.sm_tot_vol, P.d, "o-")
        plt.plot(
            [P.sm_tot_wavg_vol, P.sm_tot_wavg_vol],
            [0, P.D86],
            "v--",
            color="black",
            ms=10,
        )
    plt.xlim(0, 1)
    plt.ylim(60, 0)
    plt.xlabel("SM")
    plt.ylabel("Depth (cm)")
    plt.show()

# %%
# Plot horizontal profiles
for index, row in df.iterrows():
    plt.title(
        "SM profile locations and vertical wt. avg. SM,\nhorizontal wt. avg. SM, CRNS footprint"
    )
    for P in row["profiles"]:
        plt.plot(P.r, P.sm_tot_wavg_vol, "o-")
        plt.plot(
            [0, row["footprint_radius"]],
            [row["sm_tot_wavg_vol"], row["sm_tot_wavg_vol"]],
            ">--",
            color="black",
            ms=10,
        )
    plt.xlim(0, 250)
    plt.ylim(0.0, 1.0)
    plt.xlabel("Distance (m)")
    plt.ylabel("SM")
    plt.show()


# %%
label1 = True
for index, row in df.iterrows():
    for P in row["profiles"]:
        if label1:
            label = "Individual profiles"
            label1 = False
        else:
            label = None
        plt.scatter(
            row["calibration_day"],
            P.sm_tot_wavg_vol,
            color="black",
            s=1,
            label=label,
        )
plt.scatter(
    df.calibration_day,
    df.sm_tot_wavg_vol,
    # alpha=0.1,
    marker="o",
    fc="none",
    ec="k",
    s=50,
    label="Areal weighted average",
)

plt.legend()
plt.ylim(0.0, 1.0)
plt.show()

# %%
plt.plot(
    CRNS_data.index,
    CRNS_data.SoilMoisture_volumetric_MovAvg24h,
    # alpha=0.1,
    label="sm",
    zorder=1,
)
plt.scatter(
    df.calibration_day,
    df.sm_tot_wavg_vol,
    # alpha=0.1,
    marker="o",
    fc="none",
    ec="k",
    s=50,
    label="Areal weighted average",
    zorder=2,
)
plt.legend()
plt.ylim(0.0, 1.0)
plt.show()

# %%
# %%
neutron_column = "NeutronCount_Epithermal_MovAvg24h_corrected"
airhum_column = "AirHumidity_gapfilled"

from scipy.optimize import minimize
import numpy as np


def sm_Desilets_etal_2010(neutrons, N0=1000):
    return 0.0808 / (neutrons / N0 - 0.372) - 0.115


def find_N0_error_function(N0, sm_at_calibration_days, neutrons):
    """
    This function will be minimized
    """
    sm_from_N0 = sm_Desilets_etal_2010(neutrons, N0)
    sm_from_N0_at_calibration_dates = sm_from_N0.reindex(
        sm_at_calibration_days.index, method="nearest"
    )

    errors = sm_at_calibration_days - sm_from_N0_at_calibration_dates

    rmse = np.sqrt(np.mean(errors**2))
    # chi_squared = np.sum((errors**2) / np.abs(sm_at_calibration_days))

    return rmse


Calibration_data = df.set_index("calibration_day")

N0_init = 1000
N0_bounds = (400, 4000)
result = minimize(
    find_N0_error_function,
    N0_init,
    args=(Calibration_data["sm_tot_wavg_grv"], CRNS_data[neutron_column]),
    bounds=[N0_bounds],
)

N0_optimal = result.x[0]
RMSE = result["fun"]
print(f"Optimum: N0={N0_optimal:.0f} cph, RMSE={RMSE:.3f} m³/m³")

# %%
neutron_range = np.arange(
    CRNS_data[neutron_column].min(),
    CRNS_data[neutron_column].max(),
)
sm_range = sm_Desilets_etal_2010(neutron_range, N0_optimal)

plt.plot(
    sm_range,
    neutron_range,
    # alpha=0.1,
    label=f"N0={N0_optimal:.0f} cph, RMSE={RMSE:.3f} m³/m³",
    zorder=1,
    ls="--",
    lw=1,
    color="k",
)
plt.scatter(
    df.sm_tot_wavg_grv,
    df.neutrons,
    # alpha=0.1,
    marker="o",
    fc="none",
    ec="C0",
    s=50,
    label="Calibration days",
    zorder=2,
)
plt.legend()
plt.xlim(0, 1)
plt.xlabel("Soil moisture (g/g)")
plt.ylabel("Neutrons (cph)")
plt.show()
