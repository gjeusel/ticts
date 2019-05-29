import os

from pkg_resources import DistributionNotFound, get_distribution

from .timeseries import TimeSeries
from .utils import PANDAS_IS_INSTALLED

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

if PANDAS_IS_INSTALLED:
    from .extension import to_dataframe
    TimeSeries.to_dataframe = to_dataframe
