import arrow
from sortedcontainers import SortedDict


class TimeSeries(SortedDict):
    _default_interpolate = "previous"

    def __init__(self, data={}, default=None):
        self.default = default

        cleaned_data = data
        iterable = (list, tuple, set)
        if isinstance(data, iterable):
            cleaned_data = {}
            for key, value in data:
                cleaned_data[key] = value

        super().__init__(cleaned_data)

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

        interpolate = self._default_interpolate

        if hasattr(key, '__len__'):
            if len(key) == 2:
                key, interpolate = key
            elif len(key) > 2:
                raise KeyError

        if isinstance(key, slice):
            return self.slice(key.start, key.stop, interpolate)

        if self.empty:
            if self.default:
                return self.default
            else:
                raise KeyError

        if interpolate.lower() == "previous":
            fn = self._get_previous
        elif interpolate.lower() == "linear":
            fn = self._get_linear_interpolate
        else:
            raise ValueError("'{}' interpolation unknown.".format(interpolate))

        key = arrow.get(key)
        return fn(key)

    def _get_previous(self, time):
        if time in self.keys():
            return super().__getitem__(time)

        # In this case, bisect_left == bisect_right
        idx = self.bisect_left(time)
        if idx > 0:
            idx = idx - 1
        time_idx = self.keys()[idx]
        return super().__getitem__(time_idx)

    def _get_linear_interpolate(self, time):
        raise NotImplementedError

    def slice(self, start, end, interpolate=_default_interpolate):  # noqa A003
        start = arrow.get(start)
        end = arrow.get(end)

        newts = TimeSeries(default=self.default)

        for key, value in self.items():
            if start <= key and end > key:
                newts[key] = value

        return newts

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
