from importlib import metadata

import pandas as pd

from ticts.timeseries import TimeSeries

__version__ = metadata.version("ticts")


@pd.api.extensions.register_dataframe_accessor("to_ticts")
class FromPandasDTtoTicTS:
    def __init__(self, pandas_obj: pd.Series | pd.DataFrame):
        self.obj = pandas_obj

    def __call__(self) -> TimeSeries:
        return TimeSeries(self.obj)


@pd.api.extensions.register_series_accessor("to_ticts")
class FromPandasSeriestoTicTS:
    def __init__(self, pandas_obj: pd.Series | pd.DataFrame):
        self.obj = pandas_obj

    def __call__(self) -> TimeSeries:
        return TimeSeries(self.obj)
