# %%
import numpy as np
import pandas
import matplotlib.pyplot as plt
from neptoon.corrections.calibration_functions import Schroen2017
from pathlib import Path
from neptoon.calibration.station_calibration import (
    PrepareCalibrationData,
    CalibrationWeightsCalculator,
    PrepareNeutronCorrectedData,
    CalibrationConfiguration,
    CalibrationStation,
)


# %%

calibration_data = pandas.read_csv(
    (
        Path.cwd()
        / Path("tests/calibration/mock_data/Sheepdrove2-calibration.csv")
    ),
    skipinitialspace=True,
)
crns_data = pandas.read_csv(
    Path.cwd() / Path("tests/calibration/mock_data/Sheepdrove2-CRNS.csv"),
    index_col=0,
    parse_dates=True,
)

calib_config = CalibrationConfiguration(
    date_time_column_name="DateTime_utc",
    distance_column="Distance_to_CRNS_m",
    sample_depth_column="Profile_Depth_cm",
    bulk_density_of_sample_column="DryBulkDensity_g_cm3",
    soil_moisture_gravimetric_column="SoilMoisture_g_g",
    soil_organic_carbon_column="SoilOrganicCarbon_g_g",
    lattice_water_column="LatticeWater_g_g",
    profile_id_column="Profile_ID",
    air_humidity_column_name="AirHumidity_gapfilled",
    neutron_column_name="NeutronCount_Epithermal_MovAvg24h_corrected",
)
# %%

calibration_station = CalibrationStation(
    calibration_data=calibration_data,
    time_series_data=crns_data,
    config=calib_config,
)
estimate_n0 = calibration_station.find_n0_value()
print(f"N0 number is {estimate_n0}")
calibration_station.return_calibration_results_data_frame()
# %%
"""

Run above this line. 

I've left the plot scripts below here, they are likely broken when used
in the refactored claibration routine. We can fix them up later.



















"""

# %%

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
