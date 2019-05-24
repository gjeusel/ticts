from copy import deepcopy
from unittest import mock

import pytest
from ticts import TimeSeries

from .conftest import CURRENT, ONEHOUR, ONEMIN


class TestTimeSeriesInit:
    def test_with_data_as_dict(self, smalldict):
        ts = TimeSeries(data=smalldict)
        assert ts[CURRENT + ONEHOUR] == 1

    def test_with_data_as_tuple(self):
        ts = TimeSeries(data=((CURRENT, 0), (CURRENT + ONEHOUR, 1)))
        assert ts[CURRENT] == 0
        assert ts[CURRENT + ONEHOUR] == 1
        assert len(ts) == 2


class TestTimeSeriesGetitem:
    @mock.patch("ticts.TimeSeries._get_previous")
    def test_get_default_on_previous(self, _get_previous, smallts):
        smallts[CURRENT]
        assert _get_previous.call_count == 1

    def test_get_on_previous(self, smallts):
        assert smallts[CURRENT + ONEMIN] == 0

    def test_get_on_previous_out_of_left_bound(self, smallts):
        assert smallts[CURRENT - ONEMIN] == 0

    def test_get_on_previous_out_of_right_bound(self, smallts):
        assert smallts[CURRENT + 10 * ONEHOUR] == 9

    def test_get_on_previous_on_emtpy_raises_keyerror(self, emptyts):
        with pytest.raises(KeyError):
            assert emptyts[CURRENT]

    def test_get_on_previous_on_emtpy_with_default_return_default(
            self, emptyts_withdefault):
        assert emptyts_withdefault[CURRENT] == emptyts_withdefault.default

    def test_get_linear_interpolate_raises(self, smallts):
        with pytest.raises(NotImplementedError):
            smallts[CURRENT, "linear"]

    def test_get_on_slice_exclude_upper_bound(self, smallts):
        data = {
            CURRENT: 0,
            CURRENT + ONEHOUR: 1,
        }
        expected_ts = TimeSeries(
            data=data,
            default=smallts.default,
        )
        assert smallts[CURRENT:CURRENT + 2 * ONEHOUR] == expected_ts


def test_timeseries_set(smallts):
    smallts[CURRENT] = 1000
    assert smallts[CURRENT] == 1000


def test_timeseries_compact(smallts):
    modified = deepcopy(smallts)
    modified.set(CURRENT + ONEMIN, 0)
    assert smallts == modified.compact()
