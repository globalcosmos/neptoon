import pandas as pd

""" 
Features:
    - Class for smoothing
    - neutrons and SM need "FINAL" ColumnInfo.Name variables
    - update feature to ensure code works on most current version of
      variable
    - method to ensure ColumnInfo is managed correctly
 """


class SmoothData:
    def __init__(
        self,
        data,
        smooth_method: str,
        **kwargs,
    ):
        pass

    def apply_smoothing(self):
        pass

    def update_column_name_config(self):
        """
        This method will update the ConfigInfo.Name.... Final column
        """
