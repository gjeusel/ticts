import arrow
from sortedcontainers import SortedDict


class TimeSeries(SortedDict):
    def __init__(self, default=None, *args, **kwargs):
        self.default = default
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        key = arrow.get(key)
        super().__setitem__(key, value)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError("Can't compare TimeSeries with {}".format(
                type(other)))
        return super().__eq__(other) and self.default == other.default

    def __getitem__(self, key):
        """Get the value of the time series, even in-between measured values by interpolation.
        Args:
            key (datetime): datetime index
            interpolate (str): interpolate operator among ["previous", "linear"]
        """

        interpolate = "linear"
        if len(key) == 2:
            key, interpolate = key
        elif len(key) > 2:
            raise KeyError

        if interpolate.lower() == "previous":
            fn = self._get_previous
        elif interpolate.lower() == "linear":
            fn = self._get_linear_interpolate
        else:
            raise ValueError("'{}' interpolation unknown.".format(interpolate))

        return fn(key)

    def _get_previous(self, time):
        idx = self.bisect_left(time)
        idx = max(0, idx - 1)
        time_idx = self.keys()[idx]
        return super().__getitem__(time_idx)

    def _get_linear_interpolate(self, time):
        raise NotImplementedError

    @property
    def empty(self):
        return len(self) == 0

    def compact(self):
        """Convert this instance to a compact version: consecutive measurement of the
        same value are discarded."""
        ts = TimeSeries(default=self.default)
        for time, value in self.items():
            should_set_it = ts.empty or (ts.get(time) != value)
            if should_set_it:
                ts.set(time, value)
        return ts
