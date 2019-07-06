import operator

import pandas as pd


def timestamp_converter(ts):
    try:  # in case ts is a timestamp (also called epoch)
        ts = pd.to_datetime(float(ts), unit='ns')
    except Exception:
        ts = pd.Timestamp(ts)

    if not ts.tz:
        ts = ts.tz_localize('UTC')
    return ts


MINTS = pd.Timestamp.min.tz_localize('UTC')
MAXTS = pd.Timestamp.max.tz_localize('UTC')


class NoDefault():
    def __repr__(self):
        return 'No default'


NO_DEFAULT = NoDefault()


def operation_factory(operation):
    def fn_operation(self, other):
        return self._operate(other, getattr(operator, operation))

    return fn_operation
