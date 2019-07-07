import pandas as pd

from ticts import testing


def test_to_dataframe(smallts):
    smallts.name = 'SuperTS'
    df = smallts.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert df.columns.to_list() == ['SuperTS']


def test_from_df_to_ticst(smallts):
    df = smallts.to_dataframe()
    returned = df.to_ticts()
    testing.assert_ts_equal(smallts, returned)


def test_from_series_to_ticst(smallts):
    serie = smallts.to_dataframe()['value']
    returned = serie.to_ticts()
    testing.assert_ts_equal(smallts, returned)
