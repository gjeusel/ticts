import arrow
from sortedcontainers import SortedDict


class TimeSeries:
    def __init__(self, data=None, default=None):
        formatted_data = {}
        if data:
            for key, value in data.items():
                formatted_data[arrow.get(key)] = value

        self._data = SortedDict(formatted_data)
        self.default = default

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def items(self):
        return self._data.items()

    def __getitem__(self, time):
        return self._data[time]

    def __bool__(self):
        return bool(self._data)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError("Can't compare TimeSeries with {}".format(type(other)))
        return self._data == other._data and self.default == other.default

    def _get_previous(self, time):
        idx = self._data.bisect_left(time)
        idx = max(0, idx - 1)
        time_idx = self._data.keys()[idx]
        return self._data[time_idx]

    def _get_linear_interpolate(self, time):
        raise NotImplementedError

    def get(self, time, interpolate="previous"):
        """Get the value of the time series, even in-between measured values by interpolation.
        Args:
            time (datetime): datetime index
            interpolate (str): interpolate operator among ["previous", "linear"]
        """

        if interpolate.lower() == "previous":
            fn = self._get_previous
        elif interpolate.lower() == "linear":
            fn = self._get_linear_interpolate
        else:
            raise ValueError("'{}' interpolation unknown.".format(interpolate))

        return fn(time)

    @property
    def empty(self):
        return len(self) == 0

    def set(self, time, value):
        """Set the value for the time series.

        Args:
            time (datetime): datetime index
            value: the value
            compact (bool): if should set it even though the last entry is of the same value.
        """
        time = arrow.get(time)
        self._data[time] = value

    def compact(self):
        """Convert this instance to a compact version: consecutive measurement of the
        same value are discarded."""
        ts = TimeSeries(default=self.default)
        for time, value in self.items():
            should_set_it = ts.empty or (ts.get(time) != value)
            if should_set_it:
                ts.set(time, value)
        return ts
