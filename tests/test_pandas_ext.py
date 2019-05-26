import pandas as pd


def test_to_dataframe(smallts):
    df = smallts.to_dataframe()
    assert isinstance(df, pd.DataFrame)
