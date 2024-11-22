import streamlit as st
import pandas
import numpy as np

df = pandas.read_csv(
    "example_process/example_data/roving.csv", index_col=0, parse_dates=True
)

# df = pd.DataFrame(
#     {
#         "Neutrons": np.random.randn(1000) / 50 + 37.76,
#         "col4": np.random.rand(1000, 4).tolist(),
#     }
# )

import matplotlib.pyplot as plt

cmap = plt.get_cmap("Spectral")
sm_max = df["moisture_vol"].max()
sm_min = df["moisture_vol"].min()
df["colors"] = [
    cmap((x - sm_min) / (sm_max - sm_min)) for x in df["moisture_vol"].values
]
st.map(
    df,
    latitude="lat",
    longitude="lon",
    # x=3,
    size="col3",
    color="colors",
)
cmap(0.1)
