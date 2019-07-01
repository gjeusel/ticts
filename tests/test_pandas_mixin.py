import pandas as pd


def test_to_dataframe(smallts):
    smallts.name = 'SuperTS'
    df = smallts.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert df.columns.to_list() == ['SuperTS']
