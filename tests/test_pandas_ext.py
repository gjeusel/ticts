def test_to_dataframe(smallts, smalldict):
    df = smallts.to_dataframe()
    assert df.to_dict()['value'] == smalldict
