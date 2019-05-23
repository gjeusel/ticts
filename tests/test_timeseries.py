from copy import deepcopy
from unittest import mock

from .conftest import CURRENT, ONEHOUR, ONEMIN


class TestTimeSeriesGet:
    @mock.patch('ticts.TimeSeries._get_previous')
    def test_timeseries_get_default_on_previous(self, _get_previous, smallts):
        smallts.get(CURRENT)
        assert _get_previous.call_count == 1

    def test_timeseries_get_on_previous(self, smallts):
        assert smallts.get(CURRENT + ONEMIN) == 0

    def test_timeseries_get_on_previous_out_of_left_bound(self, smallts):
        assert smallts.get(CURRENT - ONEMIN) == 0

    def test_timeseries_get_on_previous_out_of_right_bound(self, smallts):
        assert smallts.get(CURRENT + 10 * ONEHOUR) == 9


def test_timeseries_set(smallts):
    smallts.set(CURRENT, 1000)
    assert smallts[CURRENT] == 1000


def test_timeseries_compact(smallts):
    modified = deepcopy(smallts)
    modified.set(CURRENT + ONEMIN, 0)
    assert smallts == modified.compact()
