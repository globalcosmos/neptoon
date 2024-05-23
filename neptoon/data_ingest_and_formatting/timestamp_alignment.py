from saqc import SaQC
import pandas as pd

"""
We can use SaQC to align timestamps, this could be using same method for
all cols, or vary the method based on the value (e.g., interpolate for
SM, floor for Precipt etc.). We can use nshift (nearest shift) to begin
with?
"""

data = pd.read_csv(
    "https://git.ufz.de/rdm-software/saqc/raw/develop/docs/resources/data/data.csv",
    index_col=0,
    parse_dates=True,
)

qc = SaQC(data, scheme="simple")

data.columns
qc = qc.align(field=data.columns, freq="10Min", method="nshift")
