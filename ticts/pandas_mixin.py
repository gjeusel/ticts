import pandas as pd


class PandasMixin:
    def to_dataframe(self):
        return pd.DataFrame(data={'value': self.values()}, index=self.keys())
