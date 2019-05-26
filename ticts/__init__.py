import os

from pkg_resources import DistributionNotFound, get_distribution

from . import pandas_ext
from .timeseries import TimeSeries

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

if pandas_ext.PANDAS_IS_INSTALLED:
    TimeSeries.to_dataframe = pandas_ext.to_dataframe
