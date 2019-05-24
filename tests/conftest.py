from datetime import timedelta

import pytest
from arrow import Arrow

from ticts import TimeSeries

CURRENT = Arrow(2019, 1, 1)
ONEHOUR = timedelta(hours=1)
ONEMIN = timedelta(minutes=1)


@pytest.fixture
def smalldict():
    dct = dict()
    for i in range(10):
        dct[CURRENT + i * ONEHOUR] = i
    return dct


@pytest.fixture
def smallts():
    ts = TimeSeries()
    for i in range(10):
        ts[CURRENT + i * ONEHOUR] = i
    return ts


@pytest.fixture
def emptyts():
    return TimeSeries()


@pytest.fixture
def emptyts_withdefault():
    return TimeSeries(default=10)
