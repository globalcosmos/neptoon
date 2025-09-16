# Smoothing Neutron Data

Data smoothing helps to reduce some of the inherent noise in neutron counts and is recommended during processing. It is recommended to undertake smoothing *after* corrections have been applied. This ensure that the smoothing occurs on the actual neutron responses to soil moisture changes (otherwise we would be adding external influences of soil moisture into the smoothed dataset).

In your pipeline smoothing is undertaken with this:

```python
smooth_method = "rolling_mean"
window = "12h"
min_proportion_good_data = 0.7

data_hub.smooth_data(
    column_to_smooth=str(ColumnInfo.Name.CORRECTED),
    smooth_method=smooth_method,
    window=window,
    min_proportion_good_data=min_proportion_good_data,
)

```

For now we support rolling average only - future work will integrate savitsky-golay smoothing. This algorithm is presumed to be better at preserving the peaks however requires additional processing (namely interpolation) to work. The window should be given in pandas Time format such as "12h" or "1d". Minimum proportion of good data means that the averaging is only completed when the proportion of available (non nan) data points in the window is greater than the amount presented. Recommended at 70%.