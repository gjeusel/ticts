from copy import deepcopy
from unittest import mock

import pytest

from .conftest import CURRENT, ONEHOUR, ONEMIN


class TestTimeSeriesGetitem:
    @mock.patch("ticts.TimeSeries._get_previous")
    def test_timeseries_get_default_on_previous(self, _get_previous, smallts):
        smallts[CURRENT]
        assert _get_previous.call_count == 1

    def test_timeseries_get_on_previous(self, smallts):
        assert smallts[CURRENT + ONEMIN] == 0

    def test_timeseries_get_on_previous_out_of_left_bound(self, smallts):
        assert smallts[CURRENT - ONEMIN] == 0

    def test_timeseries_get_on_previous_out_of_right_bound(self, smallts):
        assert smallts[CURRENT + 10 * ONEHOUR] == 9

    def test_timeseries_get_linear_interpolate_raises(self, smallts):
        with pytest.raises(NotImplementedError):
            smallts[CURRENT, "linear"]


def test_timeseries_set(smallts):
    smallts[CURRENT] = 1000
    assert smallts[CURRENT] == 1000


def test_timeseries_compact(smallts):
    modified = deepcopy(smallts)
    modified.set(CURRENT + ONEMIN, 0)
    assert smallts == modified.compact()
