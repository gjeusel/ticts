from datetime import timedelta

import pytest
from arrow import Arrow
from ticts import TimeSeries

CURRENT = Arrow(2019, 1, 1)
ONEHOUR = timedelta(hours=1)
ONEMIN = timedelta(minutes=1)


@pytest.fixture
def smallts():
    ts = TimeSeries()
    for i in range(10):
        ts[CURRENT + i * ONEHOUR] = i

    return ts
