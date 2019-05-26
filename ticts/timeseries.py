import logging
import operator
from datetime import timedelta

import arrow
from sortedcontainers import SortedDict

logger = logging.getLogger(__name__)


def operation_factory(operation):
    def fn_operation(self, other):
        return self._operate(other, getattr(operator, operation))

    return fn_operation


class TimeSeries(SortedDict):
    _default_interpolate = "previous"

    def __init__(self, *args, **kwargs):
        self.default = kwargs.pop('default', None)
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            return self.set_interval(key.start, key.stop, value)
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

        basemsg = "Getting {} but default attribute is not set".format(key)
        if self.empty:
            if self.default:
                return self.default
            else:
                raise KeyError("{} and timeseries is empty".format(basemsg))

        if key < self.keys()[0]:
            if self.default:
                return self.default
            else:
                msg = "{}, can't deduce value before the oldest measurement"
                raise KeyError(msg.format(basemsg))

        # If the key is already defined:
        if key in self.keys():
            return super().__getitem__(key)

        if interpolate.lower() == "previous":
            fn = self._get_previous
        elif interpolate.lower() == "linear":
            fn = self._get_linear_interpolate
        else:
            raise ValueError("'{}' interpolation unknown.".format(interpolate))

        key = arrow.get(key)
        return fn(key)

    def _get_previous(self, time):
        # In this case, bisect_left == bisect_right
        # And idx > 0 as we already handled other cases
        previous_idx = self.bisect_left(time) - 1
        time_idx = self.keys()[previous_idx]
        return super().__getitem__(time_idx)

    def _get_linear_interpolate(self, time):
        idx = self.bisect_left(time)
        previous_time_idx = self.keys()[idx - 1]

        # out of right bound case:
        if idx == len(self):
            msg = "Can't interpolate out of right bound, returning value of right bound."
            logger.info(msg)
            return super().__getitem__(previous_time_idx)

        next_time_idx = self.keys()[idx]

        previous_value = super().__getitem__(previous_time_idx)
        next_value = super().__getitem__(next_time_idx)

        coeff = (time - previous_time_idx) / (
            next_time_idx - previous_time_idx)

        value = previous_value + coeff * (next_value - previous_value)
        return value

    def slice(self, start, end, interpolate=_default_interpolate):  # noqa A003
        start = arrow.get(start)
        end = arrow.get(end)

        newts = TimeSeries(default=self.default)

        for key, value in self.items():
            if start <= key and end > key:
                newts[key] = value

        return newts

    def set_interval(self, start, end, value):
        if self.empty:
            self[start] = value
            if self.default:
                self[end] = self.default
            else:
                msg = ('You may want to set a default when setting intervals'
                       ' on empty TimeSeries')
                logger.info(msg)
            return

        entered_bound = False
        to_delete_keys = []  # avoid changing self while looping
        prev_value = None  # keep track of previous val
        for key, val in self.items():
            in_bound = (key >= start and key < end)
            if not in_bound:
                if not entered_bound:
                    continue
                else:
                    if key == end:
                        prev_value = val
                    break

            entered_bound = True
            prev_value = val
            to_delete_keys.append(key)

        for key in to_delete_keys:
            self.pop(key)

        self[start] = value
        self[end] = prev_value  # don't forget to set back last val

    def _operate(self, other, operator):
        if isinstance(other, self.__class__):
            return self._operate_on_ts(other, operator)
        else:
            return self._operate_on_one_value(other, operator)

    def _operate_on_ts(self, other, operator):
        if not isinstance(other, self.__class__):
            raise TypeError

        all_keys = set(self.keys()).union(set(other.keys()))

        default = None
        if self.default and other.default:
            default = operator(self.default, other.default)

        ts = TimeSeries(default=default)
        for key in all_keys:
            ts[key] = operator(self[key], other[key])

        return ts

    def _operate_on_one_value(self, value, operator):
        sample_value = self.values()[0]
        try:
            operator(value, sample_value)
        except Exception:
            msg = "Can't apply {} on {} with {}"
            raise TypeError(
                msg.format(operator.__name__, type(sample_value), type(value)))

        default = None
        if self.default:
            default = operator(self.default, value)

        ts = TimeSeries(default=default)
        for key in self.keys():
            ts[key] = operator(self[key], value)

        return ts

    __add__ = operation_factory('__add__')
    __sub__ = operation_factory('__sub__')
    __mul__ = operation_factory('__mul__')
    __div__ = operation_factory('__div__')

    def floor(self, other):
        return self._operate(other, min)

    def ceil(self, other):
        return self._operate(other, max)

    @property
    def empty(self):
        return len(self) == 0

    def compact(self):
        """Convert this instance to a compact version: consecutive measurement of the
        same value are discarded."""
        ts = TimeSeries(default=self.default)
        for time, value in self.items():
            should_set_it = ts.empty or (ts[time] != value)
            if should_set_it:
                ts[time] = value
        return ts

    def sample(self,
               freq,
               start=None,
               end=None,
               interpolate=_default_interpolate):
        if not isinstance(freq, timedelta):
            msg = 'Freq should be of instance timedelta, got {}'
            raise TypeError(msg.format(type(freq)))

        if not start:
            start = self.keys()[0]
        if not end:
            # Assumption last interval is [end : end + freq[
            end = self.keys()[-1] + freq

        ts = TimeSeries(default=self.default)
        for i in range(0, int((end - start) / freq)):
            dt = start + i * freq
            ts[dt] = self[dt, interpolate]

        return ts
