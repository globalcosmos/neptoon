!!! info "Work in Progress"
	Please check back soon



## Creating Custom Corrections

You can implement custom correction theories by extending the `Correction` base class:

```python
from neptoon.corrections import Correction, CorrectionType
import pandas as pd

class NewIdeaForBiomass(Correction):
    """
    My new idea to correct for biomass with humidity
    """

    def __init__(self, 
                correction_type = CorrectionType.CUSTOM,
                correction_factor_column_name: str = "new_biomass_correction",
                ):
        
        super().__init__(correction_type=correction_type, 
                         correction_factor_column_name=correction_factor_column_name)
        
        self.humidity_column_name = "air_relative_humidity"
        self.biomass_column_name = "site_biomass"

    @staticmethod
    def new_func(biomass, humidity):
        if biomass == 0:
            return 1
        return 1-((biomass / humidity) / 1000)

    def apply(self, data_frame: pd.DataFrame):

        data_frame[self.correction_factor_column_name] = data_frame.apply(
            lambda row: self.new_func(
                row[self.humidity_column_name],
                row[self.biomass_column_name], 
            ),
            axis=1,
        )
        return data_frame
```

Register your custom correction with the factory:

```python
data_hub.correction_factory.register_custom_correction(
    correction_type=CorrectionType.CUSTOM,
    theory="my_new_idea",
    correction_class=NewIdeaForBiomass,
)

data_hub.select_correction(
    correction_type=CorrectionType.CUSTOM,
    correction_theory="my_new_idea",
)

# data_hub.prepare_static_values()
data_hub.correct_neutrons()
data_hub.crns_data_frame
```