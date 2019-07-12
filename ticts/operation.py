from .utils import MINTS, NO_DEFAULT, operation_factory


def _get_keys_for_operation(ts1, ts2, *args):
    all_ts = [ts1, ts2, *args]
    for ts in all_ts:
        if not ts.__class__.__name__ == 'TimeSeries':
            raise TypeError("{} is not of type TimeSeries".format(ts))

    all_keys = set.union(*[set(ts.keys()) for ts in all_ts])

    lower_bound = MINTS
    for ts in all_ts:
        if not ts._has_default:
            lower_bound = max(lower_bound, ts.lower_bound)

    return [key for key in all_keys if key >= lower_bound]


class TictsOperationMixin:
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

        ts = self.__class__(default=default)
        for key in all_keys:
            ts[key] = operator(self[key], other[key])

        return ts

    def _operate_on_one_value(self, value, operator):
        sample_value = self.values()[0]
        try:
            operator(sample_value, value)
        except Exception:
            msg = "Can't apply {} on {} with {}"
            raise TypeError(
                msg.format(operator.__name__, type(sample_value), type(value)))

        default = None
        if self._has_default:
            default = operator(self.default, value)

        ts = self.__class__(default=default)
        for key in self.keys():
            ts[key] = operator(self[key], value)

        return ts

    __add__ = operation_factory('__add__')
    __radd__ = operation_factory('__add__')
    __sub__ = operation_factory('__sub__')

    __mul__ = operation_factory('__mul__')
    __truediv__ = operation_factory('__truediv__')
    __floordiv__ = operation_factory('__floordiv__')

    __abs__ = operation_factory('__abs__')

    __lt__ = operation_factory('__lt__')
    __le__ = operation_factory('__le__')
    __gt__ = operation_factory('__gt__')
    __ge__ = operation_factory('__ge__')
    __eq__ = operation_factory('__eq__')

    __or__ = operation_factory('__or__')
    __xor__ = operation_factory('__xor__')
    __and__ = operation_factory('__and__')

    __inv__ = operation_factory('__inv__')
    __not__ = operation_factory('__not__')

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
        if not isinstance(other, self.__class__):
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
