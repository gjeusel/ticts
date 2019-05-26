try:
    PANDAS_IS_INSTALLED = True
    import pandas as pd
except ImportError:
    PANDAS_IS_INSTALLED = False


def to_dataframe(self):
    return pd.DataFrame(data={'value': self.values()}, index=self.keys())
