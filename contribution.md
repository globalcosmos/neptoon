# This is the contribution document



## Importing functions
When importing functions to keep things organised we use the following order:

1. import x
2. from x import y
3. from neptoon import y

When importing from neptoon please always import classes and functions directly (i.e., do not use `from neptoon.x import *`)
When importing multiple classes or functions from a module use brackets and list them veritcally.

For example:

```python
import pandas as pd
import another_package

from pathlib import Path
from a_different_package import some_function

from neptoon.configuration.yaml_classes import (
    GeneralSiteMetadata,
    CRNSSensorInformation,
    TimeseriesDataFormat
)
```