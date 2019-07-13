import pandas as pd
from pandas.tseries.frequencies import to_offset

from .utils import timestamp_converter


class PandasMixin:
    def to_dataframe(self):
        return pd.DataFrame(data={self.name: self.values()}, index=self.index)

    def sample(self,
               freq=None,
               start=None,
               end=None,
               index=None,
               interpolate=None):
        """Sample your timeseries into Evenly Spaced TimeSeries.

        Args:
            freq (timedelta): frequency to convert in.
            start (datetime): left bound. Default to None, which result into
                :meth:`~timeseries.TimeSeries.lower_bound`.
            end (datetime): right bound. Default to None, which result into
                :meth:`~timeseries.TimeSeries.upper_bound`.

        Returns:
            evenly-spaced timeseries.
        """

        if freq is None and index is None:
            msg = ("You should either select one frequency OR an index for "
                   "the sampling. Both are None.")
            raise Exception(msg)

        if not interpolate:
            interpolate = self._default_interpolate

        freq = to_offset(freq)

        ts = self.__class__(default=self.default)
        if self.empty:
            return ts

        if index is not None:
            for idx in index:
                ts[idx] = self[idx]
            return ts

        if start:
            start = timestamp_converter(start)
            if not self._has_default:
                start = max(start, self.lower_bound)
        else:
            start = self.lower_bound

        if end:
            end = timestamp_converter(end)
        else:
            end = self.upper_bound + freq

        dt = start
        while dt < end:
            ts[dt] = self[dt, interpolate]
            dt = dt + freq

        return ts
