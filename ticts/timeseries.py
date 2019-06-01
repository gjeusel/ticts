import logging
import operator
from copy import deepcopy
from datetime import timedelta
from itertools import chain

from sortedcontainers import SortedDict

from .utils import MAXTS, MINTS, timestamp_converter

logger = logging.getLogger(__name__)

NO_DEFAULT = object()


def operation_factory(operation):
    def fn_operation(self, other):
        return self._operate(other, getattr(operator, operation))

    return fn_operation


def _process_args(mapping=(), **kwargs):
    if isinstance(mapping, (list, tuple, set)) and len(mapping) == 1:
        mapping = mapping[0]
    if hasattr(mapping, 'items'):
        mapping = mapping.items()

    return ((timestamp_converter(k), v)
            for k, v in chain(mapping, kwargs.items()))


def _get_keys_for_operation(ts1, ts2, *args):
    all_ts = [ts1, ts2, *args]
    for ts in all_ts:
        if not isinstance(ts, TimeSeries):
            raise TypeError("{} is not of type TimeSeries".format(ts))

    all_keys = set.union(*[set(ts.keys()) for ts in all_ts])

    lower_bound = MINTS
    for ts in all_ts:
        if not ts._has_default:
            lower_bound = max(lower_bound, ts.lower_bound)

    return [key for key in all_keys if key >= lower_bound]


class TimeSeries(SortedDict):
    """ TimeSeries object.

    Args:
        default: The default value of timeseries.
        permissive (bool): Whether to allow accessing non-existing values or not.
            If is True, getting non existing item returns None.
            If is False, getting non existing item raises.
    """
    _default_interpolate = "previous"

    @property
    def lower_bound(self):
        """Return the lower bound time index."""
        if self.empty:
            return MINTS
        return self.keys()[0]

    @property
    def upper_bound(self):
        """Return the upper bound time index."""
        if self.empty:
            return MAXTS
        return self.keys()[-1]

    @property
    def _has_default(self):
        return self.default != NO_DEFAULT

    @property
    def empty(self):
        """Return whether the TimeSeries is empty or not."""
        return len(self) == 0

    def __init__(self, *args, **kwargs):
        """"""
        self.default = kwargs.pop('default', NO_DEFAULT)
        self.permissive = kwargs.pop('permissive', True)

        # SortedDict use the first arg given and check if is a callable
        # in case you want to give your custom sorting function.
        if args and (args[0] is None or callable(args[0])):
            args = args[1:]

        # SortedDict.__init__ does not use the __setitem__
        # Hence we got to parse datetime keys ourselves.
        super().__init__(_process_args(args, **kwargs))

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            return self.set_interval(key.start, key.stop, value)
        key = timestamp_converter(key)
        super().__setitem__(key, value)

    def __getitem__(self, key):
        """Get the value of the time series, even in-between measured values by interpolation.
        Args:
            key (datetime): datetime index
            interpolate (str): interpolate operator among ["previous", "linear"]
        """

        interpolate = self._default_interpolate

        if isinstance(key, tuple):
            if len(key) == 2:
                key, interpolate = key
            elif len(key) > 2:
                raise KeyError

        if isinstance(key, slice):
            return self.slice(key.start, key.stop)

        key = timestamp_converter(key)

        basemsg = "Getting {} but default attribute is not set".format(key)
        if self.empty:
            if self._has_default:
                return self.default
            else:
                if self.permissive:
                    return
                else:
                    raise KeyError(
                        "{} and timeseries is empty".format(basemsg))

        if key < self.lower_bound:
            if self._has_default:
                return self.default
            else:
                if self.permissive:
                    return
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

        key = timestamp_converter(key)
        return fn(key)

    def _get_previous(self, time):
        # In this case, bisect_left == bisect_right
        # And idx > 0 as we already handled other cases
        previous_idx = self.bisect_left(time) - 1
        time_idx = self.keys()[previous_idx]
        return super().__getitem__(time_idx)

    def _get_linear_interpolate(self, time):
        # TODO: put it into a 'get_previous_index' method
        idx = self.bisect_left(time)
        previous_time_idx = self.keys()[idx - 1]

        # TODO: check on left bound case

        # out of right bound case:
        if idx == len(self):
            return super().__getitem__(previous_time_idx)

        next_time_idx = self.keys()[idx]

        previous_value = super().__getitem__(previous_time_idx)
        next_value = super().__getitem__(next_time_idx)

        coeff = (time - previous_time_idx) / (
            next_time_idx - previous_time_idx)

        value = previous_value + coeff * (next_value - previous_value)
        return value

    def slice(self, start, end):  # noqa A003
        """Slice your timeseries for give interval.

        Args:
            start (datetime or str): lower bound
            end (datetime or str): upper bound

        Returns:
            TimeSeries sliced
        """
        start = timestamp_converter(start)
        end = timestamp_converter(end)

        newts = TimeSeries(default=self.default)

        for key, value in self.items():
            if start <= key < end:
                newts[key] = value

        should_add_left_closure = (start not in newts.keys()
                                   and start >= self.lower_bound)
        if should_add_left_closure:
            newts[start] = self[start]  # is applying get_previous on self

        return newts

    def set_interval(self, start, end, value):
        """Set a value for an interval of time.

        Args:
            start (datetime or str): lower bound
            end (datetime or str): upper bound
            value: the value to be set

        Returns:
            self

        Raises:
            NotImplementedError: when no default is set.
        """
        if not self._has_default:
            msg = "At the moment, you have to set a default for set_interval"
            raise NotImplementedError(msg)

        start = timestamp_converter(start)
        end = timestamp_converter(end)

        sliced_ts = self.slice(start, end)
        self[start] = value

        if self.empty:
            self[end] = self.default
            return

        end_is_key = end in self.keys()
        if sliced_ts.empty:
            if not end_is_key:
                self[end] = self.default
            return

        last_value_in_bound = sliced_ts[sliced_ts.upper_bound]
        for key in sliced_ts.keys():
            self.pop(key)

        self[start] = value  # may have been popped
        if not end_is_key:  # only assign if not already defined
            self[end] = last_value_in_bound

    def _operate(self, other, operator):
        if isinstance(other, self.__class__):
            return self._operate_on_ts(other, operator)
        else:
            return self._operate_on_one_value(other, operator)

    def _operate_on_ts(self, other, operator):
        if not isinstance(other, self.__class__):
            raise TypeError

        all_keys = set(self.keys()).union(set(other.keys()))

        default = NO_DEFAULT
        if self._has_default and other._has_default:
            default = operator(self.default, other.default)

        all_keys = _get_keys_for_operation(self, other)

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
        if self._has_default:
            default = operator(self.default, value)

        ts = TimeSeries(default=default)
        for key in self.keys():
            ts[key] = operator(self[key], value)

        return ts

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError("Can't compare TimeSeries with {}".format(
                type(other)))
        return super().__eq__(other) and self.default == other.default

    def __copy__(self):
        newone = super().__copy__()
        newone.default = self.default
        return newone

    def __deepcopy__(self, memo):
        newone = deepcopy(dict(self))
        newone = TimeSeries(newone, default=self.default)
        return newone

    __add__ = operation_factory('__add__')
    __radd__ = operation_factory('__add__')

    __sub__ = operation_factory('__sub__')
    __mul__ = operation_factory('__mul__')
    __div__ = operation_factory('__div__')
    __lt__ = operation_factory('__lt__')
    __le__ = operation_factory('__le__')
    __gt__ = operation_factory('__gt__')
    __ge__ = operation_factory('__ge__')

    def floor(self, other):
        """Floor your timeseries, applying a min key by key.

        Args:
            other (TimeSeries or numeric): values to floor on.

        Returns:
            TimeSeries floored
        """
        return self._operate(other, min)

    def ceil(self, other):
        """Ceil your timeseries, applying a max key by key.

        Args:
            other (TimeSeries or numeric): values to ceil on.

        Returns:
            TimeSeries ceiled
        """
        return self._operate(other, max)

    def mask_update(self, other, mask):
        """Update your timeseries with another one in regards of a mask.

        Args:
            other (TimeSeries): values taken to update.
            mask (TimeSeries): timeseries with boolean values.

        Returns:
            TimeSeries
        """
        # Type checks
        if not isinstance(other, TimeSeries):
            msg = 'other should be of type TimeSeries, got {}'
            raise TypeError(msg.format(type(other)))

        if not all([isinstance(value, bool) for value in mask.values()]):
            msg = 'The values of the mask should all be boolean.'
            raise TypeError(msg)

        # Empty ts checks
        if mask.empty and not mask._has_default:
            msg = "mask is empty and has no default set"
            raise ValueError(msg)

        if other.empty and not other._has_default:
            msg = "other is empty and has no default set"
            raise ValueError(msg)

        all_keys = _get_keys_for_operation(self, other)

        if not mask._has_default:
            all_keys = [key for key in all_keys if key >= mask.lower_bound]

        for key in all_keys:
            if mask[key]:
                self[key] = other[key]

    def compact(self):
        """Convert this instance to a compact version: consecutive measurement of the
        same value are discarded.

        Returns:
            TimeSeries
        """
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
        if not isinstance(freq, timedelta):
            msg = 'Freq should be of instance timedelta, got {}'
            raise TypeError(msg.format(type(freq)))

        ts = TimeSeries(default=self.default)

        if self.empty:
            return ts

        if start:
            start = timestamp_converter(start)
            if not self._has_default:
                start = max(start, self.lower_bound)

        if end:
            end = timestamp_converter(end)

        if not start:
            start = self.lower_bound

        if not end:
            # Assumption last interval is [end : end + freq[
            end = self.upper_bound + freq

        for i in range(0, int((end - start) / freq)):
            dt = start + i * freq
            ts[dt] = self[dt, interpolate]

        return ts

    def __repr__(self):
        header = "<TimeSeries>"
        if self._has_default:
            header = "{} (default={})".format(header, self.default)

        def generate_content(keys):
            return '\n'.join(
                ["{}: {},".format(key.isoformat(), self[key]) for key in keys])

        if len(self) < 10:
            content = generate_content(self.keys())
        else:
            content_head = generate_content(self.keys()[:5])
            content_tail = generate_content(self.keys()[-5:])
            content = "{}\n[...]\n{}".format(content_head, content_tail)

        return "{}\n{}".format(header, content)
