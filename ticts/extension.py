import pandas as pd


def to_dataframe(self):
    return pd.DataFrame(data={'value': self.values()}, index=self.keys())
