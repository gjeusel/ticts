from copy import copy, deepcopy
from datetime import datetime, timedelta
from unittest import mock

import pytest

from ticts import TimeSeries
from ticts.utils import MAXTS, MINTS, timestamp_converter

from .conftest import CURRENT, HALFHOUR, ONEHOUR, ONEMIN


class TestTimeSeriesInit:
    def test_with_dict(self, smalldict):
        ts = TimeSeries(smalldict, default=10)
        assert ts[CURRENT + ONEHOUR] == 1
        assert ts.default == 10

    def test_with_dict_keys_being_strings(self):
        dct = {
            '2019-01-01': 1,
            '2019-02-01': 2,
            timestamp_converter('2019-03-01'): 3,
        }
        ts = TimeSeries(dct, default=10)
        expected = {
            timestamp_converter(key): value
            for key, value in dct.items()
        }
        assert ts.items() == expected.items()
        assert ts.default == 10

    def test_with_dict_keys_being_strings_passed_as_kwargs(self):
        dct = {
            '2019-01-01': 1,
            '2019-02-01': 2,
            '2019-03-01': 3,
        }
        ts = TimeSeries(**dct, default=10)
        expected = {
            timestamp_converter(key): value
            for key, value in dct.items()
        }
        assert ts.items() == expected.items()
        assert ts.default == 10

    def test_with_data_as_tuple(self):
        mytuple = (
            (CURRENT, 0),
            (CURRENT + ONEHOUR, 1),
        )
        ts = TimeSeries(mytuple, default=10)
        assert ts[CURRENT] == 0
        assert ts[CURRENT + ONEHOUR] == 1
        assert len(ts) == 2
        assert ts.default == 10

    def test_with_data_as_tuple_with_strings(self):
        mytuple = (
            ('2019-01-01', 0),
            (timestamp_converter('2019-01-01'), 1),
        )
        ts = TimeSeries(*mytuple, default=10)
        expected = {timestamp_converter(key): value for key, value in mytuple}
        assert ts.items() == expected.items()
        assert ts.default == 10


class TestTimeSeriesSetItem:
    def test_simple_setitem(self, smallts):
        smallts[CURRENT] = 1000
        assert smallts[CURRENT] == 1000

    def test_consecutive_setitem(self, smallts):
        smallts[CURRENT] = 1000
        first_time = deepcopy(smallts)
        smallts[CURRENT] = 1000
        assert first_time == smallts

    @mock.patch("ticts.TimeSeries.set_interval")
    def test_setitem_on_slice_calls_set_interval(self, set_interval, smallts):
        smallts[CURRENT:CURRENT + 2 * ONEHOUR] = 1000
        assert set_interval.call_count == 1


class TestTimeSeriesCopy:
    def test_copy(self, smallts):
        copied = copy(smallts)
        assert copied == smallts

    def test_copy_with_default(self, smallts_withdefault):
        copied = copy(smallts_withdefault)
        assert copied == smallts_withdefault

    def test_deepcopy(self, smallts):
        deepcopied = deepcopy(smallts)
        assert deepcopied == smallts

    def test_deepcopy_with_default(self, smallts_withdefault):
        deepcopied = deepcopy(smallts_withdefault)
        assert deepcopied == smallts_withdefault


class TestTimeSeriesRepr:
    def test_repr_on_otherts(self, otherts):
        assert repr(otherts).count('\n') == 3

    def test_repr_on_large(self):
        dct = dict()
        for i in range(100):
            dct[CURRENT + i * ONEHOUR] = i
        ts = TimeSeries(dct)
        assert repr(ts).count('\n') == 11

    def test_repr_with_default(self, smallts_withdefault):
        assert 'default=' in repr(smallts_withdefault)


class TestTimeSeriesDefault:
    @pytest.mark.parametrize('default', [None, 0, False])
    def test_it_has_default(self, default):
        ts = TimeSeries(default=default)
        assert ts._has_default

    def test_it_has_no_default(self):
        ts = TimeSeries()
        assert not ts._has_default


class TestTimeSeriesBoundProperties:
    def test_lower_bound(self, smallts):
        assert smallts.lower_bound == smallts.keys()[0]

    def test_upper_bound(self, smallts):
        assert smallts.upper_bound == smallts.keys()[-1]

    def test_lower_bound_on_empty(self, emptyts):
        assert emptyts.lower_bound == MINTS

    def test_upper_bound_on_empty(self, emptyts):
        assert emptyts.upper_bound == MAXTS


def test_timeseries_compact(smallts):
    smallts[CURRENT + ONEMIN] = 0
    assert (CURRENT + ONEMIN) not in smallts.compact().keys()


class TestTimeSeriesGetitem:
    available_interpolate = ['previous', 'linear']

    # tests on corner cases

    def test_get_item_out_of_left_bound_with_default_zero(self):
        mytuple = ((CURRENT, 0), (CURRENT + ONEHOUR, 1))
        ts = TimeSeries(mytuple, default=0)
        assert ts[CURRENT + ONEHOUR] == 1
        assert ts[CURRENT - ONEHOUR] == 0

    def test_getitem_out_of_left_bound_with_no_default_and_permissive_return_None(
            self, smallts):
        assert smallts[CURRENT - ONEMIN] is None

    def test_getitem_out_of_left_bound_with_no_default_and_not_permissive_raises(
            self, smallts):
        smallts.permissive = False
        with pytest.raises(KeyError) as err:
            smallts[CURRENT - ONEMIN]
        assert 'default attribute is not set' in str(err)

    def test_getitem_using_str(self, smallts):
        smallts['2019-01-01'] == 0

    @pytest.mark.parametrize('interpolate', available_interpolate)
    def test_getitem_out_of_left_bound_with_default_return_default(
            self, smallts_withdefault, interpolate):
        value = smallts_withdefault[CURRENT - ONEMIN, interpolate]
        assert value == smallts_withdefault.default

    @pytest.mark.parametrize('interpolate', available_interpolate)
    def test_getitem_on_empty_when_no_default_not_permissive_raises(
            self, emptyts, interpolate):
        emptyts.permissive = False
        with pytest.raises(KeyError) as err:
            emptyts[CURRENT - ONEMIN, interpolate]

        assert str(
            "default attribute is not set and timeseries is empty") in str(err)

    @pytest.mark.parametrize('interpolate', available_interpolate)
    def test_getitem_on_empty_when_no_default_return_None(
            self, emptyts, interpolate):
        emptyts[CURRENT - ONEMIN, interpolate] is None

    # tests on '_get_previous'

    @mock.patch("ticts.TimeSeries._get_previous")
    def test_get_on_previous_is_default_interpolate(self, _get_previous,
                                                    smallts):
        smallts[CURRENT + ONEMIN]
        assert _get_previous.call_count == 1

    def test_get_on_previous(self, smallts):
        assert smallts[CURRENT + ONEMIN] == 0

    def test_get_on_previous_out_of_right_bound(self, smallts):
        assert smallts[CURRENT + 10 * ONEHOUR] == 9

    # tests on '_get_linear_interpolate'

    @pytest.mark.parametrize('time_idx, expected', [
        (CURRENT + HALFHOUR, 0.5),
        (CURRENT + ONEHOUR + HALFHOUR, 1.5),
        (CURRENT + 10 * ONEMIN, 0 + (1 - 0) * (10 * ONEMIN / ONEHOUR)),
    ])
    def test_get_linear_interpolate(self, smallts, time_idx, expected):
        assert smallts[time_idx, 'linear'] == expected

    def test_get_linear_interpolate_out_of_right_bound(self, smallts):
        assert smallts[CURRENT + 10 * ONEHOUR, 'linear'] == 9

    # test on 'slice'

    def test_get_on_slice_exclude_upper_bound_include_lower_bound(
            self, smallts):
        start = CURRENT
        end = CURRENT + 1 * ONEHOUR
        data = {start: 0, end: 1}
        expected_ts = TimeSeries(data, default=smallts.default)
        assert smallts[start:end + ONEHOUR] == expected_ts

    def test_get_on_slice_add_back_previous_value_if_start_not_in_keys(
            self, smallts):
        start = CURRENT + HALFHOUR
        end = CURRENT + ONEHOUR
        data = {start: 0, end: 1}
        expected_ts = TimeSeries(data, default=smallts.default)
        assert smallts[start:end + ONEHOUR] == expected_ts

    def test_get_on_slice_entirely_out_of_bounds_on_left_side(self, smallts):
        assert smallts[CURRENT - 2 * ONEHOUR:CURRENT - 1 * ONEHOUR].empty

    def test_get_on_slice_out_of_bounds_left_side(self, smallts):
        start = CURRENT - 2 * ONEHOUR
        end = CURRENT
        data = {CURRENT: 0}
        expected_ts = TimeSeries(data, default=smallts.default)
        assert smallts[start:end + 1 * ONEHOUR] == expected_ts

    def test_get_on_slice_entirely_out_of_bounds_on_right_side(self, smallts):
        start = CURRENT + 10 * ONEHOUR
        end = CURRENT + 12 * ONEHOUR
        expected = TimeSeries({start: smallts[start]})
        sliced = smallts[start:end]
        assert sliced == expected

    def test_get_on_slice_out_of_bounds_on_right_side(self, smallts):
        sliced_ts = smallts[CURRENT + 9 * ONEHOUR:CURRENT + 12 * ONEHOUR]
        expected_dct = {CURRENT + 9 * ONEHOUR: 9}
        expected_ts = TimeSeries(expected_dct, default=smallts.default)
        assert sliced_ts == expected_ts


class TestTimeSeriesSetInterval:
    def test_set_interval_raises_when_no_default(self, smallts):
        with pytest.raises(NotImplementedError):
            smallts.set_interval(CURRENT, CURRENT + ONEHOUR, 1000)

    def test_single_set_interval_end_on_last_key(self, smallts_withdefault):
        smallts_withdefault.set_interval(CURRENT + ONEHOUR,
                                         CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + ONEHOUR, CURRENT + 9 * ONEHOUR]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[CURRENT + ONEHOUR] == 1000

    def test_single_set_interval_start_on_first_key(self, smallts_withdefault):
        smallts_withdefault.set_interval(CURRENT, CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + 9 * ONEHOUR]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[CURRENT] == 1000

    @pytest.mark.parametrize('start, end', [
        (CURRENT + ONEHOUR, CURRENT + 10 * ONEHOUR),
        (CURRENT + 4 * ONEHOUR, CURRENT + 11 * ONEHOUR),
    ])
    def test_single_set_interval_end_over_last_key_sets_to_last_value(
            self, smallts_withdefault, start, end):
        last_key = smallts_withdefault.keys()[-1]
        last_val = smallts_withdefault[last_key]

        smallts_withdefault.set_interval(start, end, 1000)
        keys_before_start = []
        for key in smallts_withdefault.keys():
            if key < start:
                keys_before_start.append(key)

        expected_keys = [*keys_before_start, start, end]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[end] == last_val

    def test_single_set_interval_when_start_higher_than_upper_bound(
            self, smallts_withdefault):
        start = CURRENT + 11 * ONEHOUR
        end = CURRENT + 13 * ONEHOUR
        smallts_withdefault.set_interval(start, end, 1000)
        assert smallts_withdefault[CURRENT + 10 * ONEHOUR] == 9
        assert smallts_withdefault[start] == 1000
        assert smallts_withdefault[end] == 9

    def test_single_set_interval_start_before_first_key(
            self, smallts_withdefault):
        smallts_withdefault.set_interval(CURRENT - ONEHOUR,
                                         CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT - ONEHOUR, CURRENT + 9 * ONEHOUR]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[CURRENT - 1 * ONEHOUR] == 1000

    def test_single_set_interval_on_bounds_not_being_keys(
            self, smallts_withdefault):
        smallts_withdefault.set_interval(CURRENT + ONEMIN,
                                         CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + ONEMIN, CURRENT + 9 * ONEHOUR]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[CURRENT + ONEMIN] == 1000

    def test_set_interval_on_empty(self, emptyts):
        emptyts.default = 10
        emptyts.set_interval(CURRENT, CURRENT + ONEHOUR, 1)
        assert emptyts[CURRENT] == 1
        len(emptyts.keys()) == 1

    def test_set_interval_on_empty_with_default(self, emptyts_withdefault):
        emptyts_withdefault.set_interval(CURRENT, CURRENT + ONEHOUR, 1)
        assert emptyts_withdefault[CURRENT] == 1
        assert emptyts_withdefault[CURRENT +
                                   ONEHOUR] == emptyts_withdefault.default
        len(emptyts_withdefault.keys()) == 2

    @pytest.mark.parametrize('start, end', (
        (CURRENT, CURRENT + 9 * ONEHOUR),
        (CURRENT + 5 * ONEHOUR, CURRENT + 12 * ONEHOUR),
        (datetime(2019, 1, 1) + 5 * ONEHOUR,
         datetime(2019, 1, 1) + 12 * ONEHOUR),
        ('2019-01-01T05:00:00', '2019-01-01T12:00:00+02:00'),
    ))
    def test_same_consecutive_set_interval(self, smallts_withdefault, start,
                                           end):
        smallts_withdefault.set_interval(start, end, 1000)
        first_time = deepcopy(smallts_withdefault)

        for _ in range(10):
            smallts_withdefault.set_interval(start, end, 1000)

        assert first_time == smallts_withdefault

    def test_consecutive_set_interval_on_empty_with_default(self, emptyts):
        emptyts.default = 10
        emptyts.set_interval(CURRENT, CURRENT + 2 * ONEHOUR, 10)
        emptyts.set_interval(CURRENT, CURRENT + ONEHOUR, 0)
        emptyts.set_interval(CURRENT + ONEHOUR, CURRENT + 2 * ONEHOUR, 1)
        emptyts.set_interval(CURRENT, CURRENT + 2 * ONEHOUR, 3)
        assert emptyts[CURRENT] == 3
        assert emptyts[CURRENT + 2 * ONEHOUR] == 10
        assert list(emptyts.keys()) == [CURRENT, CURRENT + 2 * ONEHOUR]

    def test_set_interval_when_no_keys_to_delete_with_default(self, emptyts):
        emptyts.default = 1000
        emptyts.set_interval(CURRENT, CURRENT + 1 * ONEHOUR, 0)
        emptyts.set_interval(CURRENT + 3 * ONEHOUR, CURRENT + 4 * ONEHOUR, 3)
        emptyts.set_interval(CURRENT + 1 * ONEHOUR + HALFHOUR,
                             CURRENT + 3 * ONEHOUR, 10)

        expected_dct = {
            CURRENT: 0,
            CURRENT + 1 * ONEHOUR: 1000.,
            CURRENT + 1 * ONEHOUR + HALFHOUR: 10,
            CURRENT + 3 * ONEHOUR: 3,
            CURRENT + 4 * ONEHOUR: 1000
        }
        assert list(emptyts.keys()) == list(expected_dct.keys())

        for key in expected_dct:
            assert emptyts[key] == expected_dct[key]


class TestTimeSeriesOperators:
    def test_simple_add(self, smallts, smalldict):
        ts = smallts + smallts
        newdct = {key: value + value for key, value in smalldict.items()}
        assert ts == TimeSeries(newdct)

    def test_simple_add_one_float(self, smallts, smalldict):
        ts = smallts + 1000
        assert list(ts.values()) == list(range(1000, 1010))

    def test_add_with_keys_differences_with_default(self, smallts_withdefault,
                                                    otherts_withdefault):
        ts = smallts_withdefault + otherts_withdefault
        assert ts.default == smallts_withdefault.default + otherts_withdefault.default
        assert ts[CURRENT + 1 * ONEHOUR] == 1 + otherts_withdefault.default
        assert ts[CURRENT + 2 * ONEHOUR] == 2 + 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 + 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 + 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 + 3000

    def test_add_with_keys_differences_without_default(self, smallts, otherts):
        ts = smallts + otherts
        assert not ts._has_default
        assert CURRENT + 1 * ONEHOUR not in ts.keys()
        assert ts[CURRENT + 2 * ONEHOUR] == 2 + 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 + 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 + 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 + 3000

    def test_add_with_keys_differences_with_mixed_default_nodefault(
            self, smallts_withdefault, otherts):
        ts = smallts_withdefault + otherts
        assert not ts._has_default
        assert CURRENT + 1 * ONEHOUR not in ts.keys()
        assert ts[CURRENT + 2 * ONEHOUR] == 2 + 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 + 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 + 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 + 3000

    def test_add_on_list_of_timeseries(self, smallts):
        lst_timeseries = [smallts, smallts, smallts]
        result = sum(lst_timeseries)

        for key in result:
            assert result[key] == 3 * smallts[key]

    def test_simple_sub(self, smallts):
        ts = smallts - smallts
        assert all([val == 0 for val in ts.values()])

    def test_simple_sub_one_float(self, smallts):
        ts = smallts - 1
        assert list(ts.values()) == list(range(-1, 9))

    def test_sub_with_keys_differences_with_default(self, smallts_withdefault,
                                                    otherts_withdefault):
        ts = smallts_withdefault - otherts_withdefault
        assert ts[CURRENT + 1 * ONEHOUR] == 1 - 900
        assert ts[CURRENT + 2 * ONEHOUR] == 2 - 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 - 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 - 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 - 3000

    def test_sub_with_keys_differences_without_default(self, smallts, otherts):
        ts = smallts - otherts
        assert CURRENT + 1 * ONEHOUR not in ts.keys()
        assert ts[CURRENT + 2 * ONEHOUR] == 2 - 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 - 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 - 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 - 3000

    def test_simple_le(self, smallts):
        result = smallts >= 5
        assert all([
            not val for val in result[CURRENT:CURRENT + 4 * ONEHOUR].values()
        ])
        assert all([
            val for val in result[CURRENT + 5 * ONEHOUR:CURRENT +
                                  9 * ONEHOUR].values()
        ])

    def test_simple_lt(self, smallts):
        result = smallts > 5
        assert all([
            not val for val in result[CURRENT:CURRENT + 5 * ONEHOUR].values()
        ])
        assert all([
            val for val in result[CURRENT + 6 * ONEHOUR:CURRENT +
                                  9 * ONEHOUR].values()
        ])

    def test_floor_on_float(self, smallts):
        ts = smallts.floor(2)
        assert all([value <= 2 for value in ts.values()])

    def test_floor_on_ts(self, smallts_withdefault, otherts_withdefault):
        ts = smallts_withdefault.floor(otherts_withdefault)
        assert ts[CURRENT + 1 * ONEHOUR] == 1
        assert ts[CURRENT + 2 * ONEHOUR] == 2
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2
        assert ts[CURRENT + 3 * ONEHOUR] == 3
        assert ts[CURRENT + 4 * ONEHOUR] == 4

    def test_ceil_on_float(self, smallts):
        ts = smallts.ceil(7)
        assert all([value >= 7 for value in ts.values()])

    def test_ceil_on_ts(self, smallts_withdefault, otherts_withdefault):
        ts = smallts_withdefault.ceil(otherts_withdefault)
        assert ts[CURRENT + ONEHOUR] == 900
        assert ts[CURRENT + 2 * ONEHOUR] == 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 3000

    def test_ceil_on_ts_check_changing_default(self, smallts_withdefault,
                                               otherts_withdefault):
        otherts_withdefault.default = -10
        ts = smallts_withdefault.ceil(otherts_withdefault)

        assert ts[CURRENT + ONEHOUR] == 1
        assert ts[CURRENT + 2 * ONEHOUR] == 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 3000


class TestMaskUpdate:
    """
                0    1    2    3    4    5    6    7    8    9
                |    |    |    |    |    |    |    |    |    |    |
                ----------------------------------------------------------
    smallts     *    *    *    *    *    *    *    *    *    *
    otherts               *  *      *
    maskts                   T      F
    """

    def test_simple_mask_update_raises_on_type_of_other(self, smallts, maskts):
        with pytest.raises(TypeError) as err:
            smallts.mask_update("fakedct", maskts)

        assert "other should be of type TimeSeries, got" in str(err)

    def test_simple_mask_update_raises_if_not_boolean(self, smallts):
        with pytest.raises(TypeError) as err:
            smallts.mask_update(smallts, smallts)

        assert "The values of the mask should all be boolean" in str(err)

    def test_mask_update_with_empty_no_default_other_raises(
            self, smallts, emptyts, maskts):
        with pytest.raises(ValueError) as err:
            smallts.mask_update(emptyts, maskts)
        assert 'other is empty and has no default set' in str(err)

    def test_mask_update_with_empty_and_no_default_mask_raises(
            self, smallts, emptyts):
        with pytest.raises(ValueError) as err:
            smallts.mask_update(smallts, emptyts)
        assert 'mask is empty and has no default set' in str(err)

    def test_simple_mask_update(self, smallts, otherts, maskts):
        smallts_keys = smallts.keys()
        otherts_keys = otherts.keys()
        smallts.mask_update(otherts, maskts)

        assert set(smallts.keys()) == set(smallts_keys).union(
            set(otherts_keys))

        assert smallts[CURRENT + 2 * ONEHOUR] == 2
        assert smallts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2000
        assert smallts[CURRENT + 3 * ONEHOUR] == 2000
        assert smallts[CURRENT + 4 * ONEHOUR] == 4

    def test_mask_update_with_other_being_empty_with_default(
            self, smallts, emptyts, maskts):
        emptyts.default = -10.
        smallts.mask_update(emptyts, maskts)

        assert smallts[CURRENT + 2 * ONEHOUR] == 2
        assert smallts[CURRENT + 3 * ONEHOUR] == -10.
        assert smallts[CURRENT + 4 * ONEHOUR] == 4

    def test_mask_update_on_emptyts(self, smallts, emptyts, maskts):
        emptyts.mask_update(smallts, maskts)
        assert emptyts == TimeSeries({CURRENT + 3 * ONEHOUR: 3})


class TestTimeSeriesSample:
    def test_simple_sample_on_default(self, smallts):
        ts = smallts.sample(HALFHOUR)
        expected_dict = {
            **smallts,
            **{
                key + HALFHOUR: smallts[key]
                for key in list(smallts.keys())[:-1]
            }
        }
        expected_ts = TimeSeries(expected_dict, default=smallts.default)
        assert ts == expected_ts

    def test_simple_sample_with_start_being_string(self, smallts):
        start = '2019-01-01T09:00:00'
        ts = smallts.sample(HALFHOUR, start=start)
        assert ts == TimeSeries({start: 9})

    def test_sample_out_of_left_bound_with_no_default_permissive_shorten_interval(
            self, smallts):
        ts = smallts.sample(
            freq=HALFHOUR, start=CURRENT - ONEHOUR, end=CURRENT + ONEHOUR)
        assert ts == TimeSeries({CURRENT: 0, CURRENT + HALFHOUR: 0})

    def test_sample_on_empty_return_empty_df(self, emptyts):
        assert emptyts.sample(freq=ONEHOUR).empty

    def test_sample_with_start_out_of_left_bounds_with_default(
            self, smallts_withdefault):
        ts = smallts_withdefault.sample(freq=HALFHOUR, start=CURRENT - ONEHOUR)
        default = smallts_withdefault.default
        assert ts[CURRENT - ONEHOUR] == default
        assert ts[CURRENT - HALFHOUR] == default
        assert ts[CURRENT] == 0
        assert CURRENT + HALFHOUR in ts.keys()

    def test_sample_with_start_out_of_left_bounds(self, smallts):
        ts = smallts.sample(freq=HALFHOUR, start=CURRENT - ONEHOUR)
        CURRENT - ONEHOUR not in ts.keys()
        CURRENT - HALFHOUR not in ts.keys()
        assert ts[CURRENT] == 0
        assert CURRENT + HALFHOUR in ts.keys()

    @pytest.mark.parametrize(
        'freq', [ONEMIN, 10 * ONEMIN,
                 timedelta(seconds=10), ONEHOUR])
    def test_sample_on_freq_with_end_and_start_in_bound(self, otherts, freq):
        start = CURRENT + 2 * ONEHOUR + HALFHOUR
        end = CURRENT + 3 * ONEHOUR + HALFHOUR
        ts = otherts.sample(freq=freq, start=start, end=end)
        assert list(ts.keys()) == [
            start + i * freq for i in range(int((end - start) / freq))
        ]
