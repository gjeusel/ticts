import logging
from copy import deepcopy

import pandas as pd
import pytz
from sortedcontainers import SortedDict, SortedList

from .io import TictsIOMixin
from .operation import TictsOperationMixin
from .pandas_mixin import PandasMixin
from .utils import MAXTS, MINTS, NO_DEFAULT, timestamp_converter

logger = logging.getLogger(__name__)

DEFAULT_NAME = 'value'


def _process_args(data, tz):
    if data is None:
        data = []
    if isinstance(data, (list, tuple, set)) and len(data) == 1:
        data = data[0]

    if isinstance(data, pd.DataFrame):
        # We should already have checked len(df.columns) == 1
        data = data.to_dict()[data.columns[0]]
    elif isinstance(data, pd.Series):
        data = data.to_dict()

    if hasattr(data, 'items'):
        data = data.items()

    return ((timestamp_converter(k, tz), v) for k, v in data)


class TictsMagicMixin:
    def __copy__(self):
        return self.__class__(self)

    def __deepcopy__(self, memo):
        return TimeSeries(
            data=deepcopy(self.data),
            default=self.default,
            name=self.name,
            permissive=self.permissive)

    def __repr__(self):
        header = "<TimeSeries>"

        meta = []
        if self._has_default:
            meta.append('default={}'.format(self.default))
        if self.name != DEFAULT_NAME:
            meta.append("name='{}'".format(self.name))

        if meta:
            header = "{} ({})".format(header, ' | '.join(meta))

        def generate_content(keys):
            return '\n'.join(
                ["{}: {},".format(key.isoformat(), self[key]) for key in keys])

        if len(self) < 10:
            content = generate_content(self.index)
        else:
            content_head = generate_content(self.index[:5])
            content_tail = generate_content(self.index[-5:])
            content = "{}\n[...]\n{}".format(content_head, content_tail)

        return "{}\n{}".format(header, content)

    # Methods redirecting to SortedDict data attribute method
    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return self.data.__iter__()

    def __delitem__(self, key):
        del self.data[key]

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()


class TimeSeries(TictsMagicMixin, TictsOperationMixin, PandasMixin,
                 TictsIOMixin):
    """ TimeSeries object.

    Args:
        default: The default value of timeseries.
        permissive (bool): Whether to allow accessing non-existing values or not.
            If is True, getting non existing item returns None.
            If is False, getting non existing item raises.
    """
    _default_interpolate = "previous"

    _special_keys = ('default', 'name', 'permissive')

    @property
    def index(self):
        return self.data.keys()

    @property
    def lower_bound(self):
        """Return the lower bound time index."""
        if self.empty:
            return MINTS
        return self.index[0]

    @property
    def upper_bound(self):
        """Return the upper bound time index."""
        if self.empty:
            return MAXTS
        return self.index[-1]

    @property
    def _has_default(self):
        return self.default != NO_DEFAULT

    @property
    def empty(self):
        """Return whether the TimeSeries is empty or not."""
        return len(self) == 0

    def __init__(self,
                 data=None,
                 default=NO_DEFAULT,
                 name=DEFAULT_NAME,
                 permissive=True,
                 tz='UTC'):
        """"""
        if isinstance(data, self.__class__):
            for attr in ('data', *self._special_keys):
                setattr(self, attr, getattr(data, attr))
            return

        if hasattr(default, 'lower') and default.lower() == 'no_default':
            self.default = NO_DEFAULT
        else:
            self.default = default

        try:
            tz = pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            raise ValueError('{} is not a valid timezone'.format(tz))

        self.name = name
        self.permissive = permissive

        if isinstance(data, pd.DataFrame):
            if len(data.columns) != 1:
                msg = ("Can't convert a DataFrame with several columns into "
                       "one timeseries: {}.")
                raise Exception(msg.format(data.columns))
            self.name = data.columns[0]

        elif isinstance(data, pd.Series):
            self.name = data.name

        # SortedDict.__init__ does not use the __setitem__
        # Hence we got to parse datetime keys ourselves.
        # SortedDict use the first arg given and check if is a callable
        # in case you want to give your custom sorting function.
        self.data = SortedDict(None, _process_args(data, tz))

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            return self.set_interval(key.start, key.stop, value)
        if key in self._special_keys:
            super().__setitem__(key, value)
        else:
            key = timestamp_converter(key, self.tz)
            self.data[key] = value

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

        key = timestamp_converter(key, self.tz)

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
        if key in self.index:
            return self.data[key]

        if interpolate.lower() == "previous":
            fn = self._get_previous
        elif interpolate.lower() == "linear":
            fn = self._get_linear_interpolate
        else:
            raise ValueError("'{}' interpolation unknown.".format(interpolate))

        return fn(key)

    def _get_previous(self, time):
        # In this case, bisect_left == bisect_right == bisect
        # And idx > 0 as we already handled other cases
        previous_idx = self.data.bisect(time) - 1
        time_idx = self.index[previous_idx]
        return self.data[time_idx]

    def _get_linear_interpolate(self, time):
        # TODO: put it into a 'get_previous_index' method
        idx = self.data.bisect_left(time)
        previous_time_idx = self.index[idx - 1]

        # TODO: check on left bound case

        # out of right bound case:
        if idx == len(self):
            return self.data[previous_time_idx]

        next_time_idx = self.index[idx]

        previous_value = self.data[previous_time_idx]
        next_value = self.data[next_time_idx]

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
        start = timestamp_converter(start, self.tz)
        end = timestamp_converter(end, self.tz)

        newts = TimeSeries(default=self.default)

        for key in self.data.irange(start, end, inclusive=(True, False)):
            newts[key] = self[key]

        should_add_left_closure = (start not in newts.index
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

        start = timestamp_converter(start, self.tz)
        end = timestamp_converter(end, self.tz)

        keys = self.data.irange(start, end, inclusive=(True, False))

        last_value = self[end]

        for key in list(keys):
            del self.data[key]

        self[start] = value
        self[end] = last_value

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

    def iterintervals(self, end=None):
        """Iterator that contain start, end of intervals.

        Args:
            end (datetime): right bound of last interval.
        """
        lst_keys = SortedList(self.index)
        if not end:
            end = self.upper_bound
        else:
            end = timestamp_converter(end, self.tz)
            if end not in lst_keys:
                lst_keys.add(end)

        for i, key in enumerate(lst_keys[:-1]):
            next_key = lst_keys[i + 1]
            if next_key > end:  # stop there
                raise StopIteration
            yield key, next_key

    def equals(self, other, check_default=True, check_name=True):
        if not isinstance(other, self.__class__):
            raise TypeError("Can't compare {} with {}".format(
                self.__class__.__name__, other.__class__.__name__))

        is_equal = self.data == other.data

        if check_default:
            is_equal = is_equal and self.default == other.default

        if check_name:
            is_equal = is_equal and self.name == other.name

        return is_equal

    @property
    def tz(self):
        if self.empty:
            return pytz.UTC
        return str(self.index[0].tz)

    def tz_convert(self, tz):
        try:
            tz = pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            raise ValueError('{} is not a valid timezone'.format(tz))

        ts = deepcopy(self)

        for key in ts.index:
            ts[key.tz_convert(tz)] = ts.data.pop(key)

        return ts
