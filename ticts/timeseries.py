import logging
import operator

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
        # __init__(self, default=None, *args, **kwargs) would ne painful to use
        #
        # __init__(self, data={}, default=None, *args, **kwargs) leads to
        # issues in setting the self._key in SortedDict.__init__

        self.default = kwargs.pop('default', None)
        super().__init__(*args, **kwargs)

        # # Monkey Patching operations
        # operations = [
        #     '__add__', '__sub__', '__mul__', '__div__', '__min__', '__max__'
        # ]
        # for operation in operations:
        #     setattr(self, operation,
        #             lambda x: self._operate(x, getattr(operator, operation)))

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

        if key < self.keys()[0]:
            if self.default:
                return self.default
            else:
                msg = (
                    "'default' value is not set, hence no values are set before"
                    " the oldest measurement.")
                raise IndexError(msg)

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
