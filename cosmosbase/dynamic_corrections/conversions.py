"""
Pseudo:

Bring in the 
"""

import pandas as pd


class CalculateNeutronCorrectionFactors:
    """
    Take in a CRNSDataHub object, which contains the (at this point)
    validated and standard dataframe. Output the dataframe with
    corrections applied.

    Things to think about:
        - CRNSDataHub should contain a process metadata object that
          records what corrections where used
        - CRNSDataHub will contain a flag dataframe, a function in the
          CRNSDataHub should return the dataframe but only with the good
          data we wish to use and performa corrections on that.

    """

    def _init__(self):
        pass
