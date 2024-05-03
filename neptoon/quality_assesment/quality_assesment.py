from abc import ABC, abstractmethod
import pandas as pd


class QualityAssessmentOfDataFrame(ABC):
    """
    Base class for Quality Assessment of DataFrames. The Quality
    Assessment routine will take dataframes at various points in the
    pipeline, and conduct quality assessment on them.

    It will do two things:

    1) it will check data against rules
    2) it will create a flag dataframe if data points do not comply with
       the rules

    The flag dataframe is a mirror copy of the input dataframe, but
    instead of values it will contain flags on the data quality.

    """

    def __init__(self):
        pass
