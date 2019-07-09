import os

import pandas as pd
from pkg_resources import DistributionNotFound, get_distribution

from . import testing  # noqa: F401
from .timeseries import TimeSeries  # noqa: F401

try:
    _dist = get_distribution("ticts")

    # Normalize case for Windows systems
    dist_loc = os.path.normcase(_dist.location)
    here = os.path.normcase(__file__)

    if not here.startswith(os.path.join(dist_loc, "ticts")):
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = "Version not found."
else:
    __version__ = _dist.version


@pd.api.extensions.register_dataframe_accessor("to_ticts")
class FromPandasDTtoTicTS(object):
    def __init__(self, pandas_obj):
        self.obj = pandas_obj

    def __call__(self):
        return TimeSeries(self.obj)


@pd.api.extensions.register_series_accessor("to_ticts")
class FromPandasSeriestoTicTS(object):
    def __init__(self, pandas_obj):
        self.obj = pandas_obj

    def __call__(self):
        return TimeSeries(self.obj)
