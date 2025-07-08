import pandas as pd
import pandera.pandas as pa


def _validate_df(df: pd.DataFrame, schema: pa.DataFrameSchema):
    """
    Validates a df against a pandera.pandas DataFrameSchema

    NOTES:
    Keep it lazy to give info of all df issues

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe to validate
    schema : pa.DataFrameSchema
        Pandera Schema to check against
    """
    return schema.validate(df, lazy=True)
