import pytest

from ticts import TimeSeries, testing

from .conftest import CURRENT, HALFHOUR, ONEHOUR


class TestTictsAdd:
    def test_simple_add(self, smallts, smalldict):
        ts = smallts + smallts
        newdct = {key: value + value for key, value in smalldict.items()}
        expected_ts = TimeSeries(newdct)
        testing.assert_ts_equal(ts, expected_ts)

    def test_simple_add_one_float(self, smallts):
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


class TestTictsSub:
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

    def test_sub_with_keys_differences_with_mixed_default_nodefault(
            self, smallts_withdefault, otherts):
        ts = smallts_withdefault - otherts
        assert not ts._has_default
        assert CURRENT + 1 * ONEHOUR not in ts.keys()
        assert ts[CURRENT + 2 * ONEHOUR] == 2 - 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 - 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 - 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 - 3000


class TestTictsMul:
    def test_simple_mul(self, smallts):
        ts = smallts * smallts
        assert list(ts.values()) == [val * val for val in smallts.values()]

    def test_simple_mul_one_float(self, smallts):
        ts = smallts * 1000.
        assert list(ts.values()) == [val * 1000. for val in smallts.values()]


class TestTictsDiv:
    def test_simple_div(self, smallts):
        smallts[CURRENT] = 1  # can't divide by zero
        ts = smallts / smallts
        assert list(ts.values()) == [val / val for val in smallts.values()]

    def test_simple_div_one_float(self, smallts):
        ts = smallts / 1000.
        assert list(ts.values()) == [val / 1000. for val in smallts.values()]


class TestTictsBoolean:
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

    def test_simple_eq(self, smallts):
        ts = smallts == smallts
        assert all(ts.values())


class TestTictsFloorCeil:
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

        assert "other should be of type TimeSeries, got" in str(err.value)

    def test_simple_mask_update_raises_if_not_boolean(self, smallts):
        with pytest.raises(TypeError) as err:
            smallts.mask_update(smallts, smallts)

        assert "The values of the mask should all be boolean" in str(err.value)

    def test_mask_update_with_empty_no_default_other_raises(
            self, smallts, emptyts, maskts):
        with pytest.raises(ValueError) as err:
            smallts.mask_update(emptyts, maskts)
        assert 'other is empty and has no default set' in str(err.value)

    def test_mask_update_with_empty_and_no_default_mask_raises(
            self, smallts, emptyts):
        with pytest.raises(ValueError) as err:
            smallts.mask_update(smallts, emptyts)
        assert 'mask is empty and has no default set' in str(err.value)

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
        expected_ts = TimeSeries({CURRENT + 3 * ONEHOUR: 3})
        testing.assert_ts_equal(emptyts, expected_ts)
