import pytest
from inline_snapshot import snapshot

from tests.conftest import CURRENT, HALFHOUR, ONEHOUR
from ticts import TimeSeries, testing
from ticts.utils import NO_DEFAULT


class TestTictsAdd:
    def test_simple_add(self, smallts, smalldict):
        ts = smallts + smallts
        newdct = {key: value + value for key, value in smalldict.items()}
        expected_ts = TimeSeries(newdct)
        testing.assert_ts_equal(ts, expected_ts)

    def test_simple_add_one_float(self, smallts):
        ts = smallts + 1000
        assert list(ts.values()) == list(range(1000, 1010))

    def test_add_with_keys_differences_with_default(
        self, smallts_withdefault, otherts_withdefault
    ):
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
        assert CURRENT + 1 * ONEHOUR not in ts.index
        assert ts[CURRENT + 2 * ONEHOUR] == 2 + 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 + 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 + 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 + 3000

    def test_add_with_keys_differences_with_mixed_default_nodefault(
        self, smallts_withdefault, otherts
    ):
        ts = smallts_withdefault + otherts
        assert not ts._has_default
        assert CURRENT + 1 * ONEHOUR not in ts.index
        assert ts[CURRENT + 2 * ONEHOUR] == 2 + 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 + 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 + 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 + 3000

    def test_add_on_list_of_timeseries(self, smallts):
        lst_timeseries = [smallts, smallts, smallts]
        result = sum(lst_timeseries)

        for key in result:
            assert result[key] == 3 * smallts[key]

    def test_add_on_no_default(self):
        ts = TimeSeries({"2023-01-01": 1}, tz="CET")
        result = ts + 0
        assert result.default is NO_DEFAULT

    def test_add_when_missing_values(self):
        ts = TimeSeries({})
        with pytest.raises(TypeError, match="Can't apply"):
            ts + 0

        ts = TimeSeries({}, default=1)
        result = ts + 0
        assert result.empty

    def test_add_on_slice(self):
        ts = TimeSeries({}, default=1)
        ts[CURRENT] = 1
        ts[CURRENT + 10 * ONEHOUR] = 2
        ts[CURRENT : CURRENT + 2 * ONEHOUR] += 10
        assert dict(ts) == {
            CURRENT: 11,
            CURRENT + 2 * ONEHOUR: 1,
            CURRENT + 10 * ONEHOUR: 2,
        }
        assert all(isinstance(val, int) for val in ts.values())


class TestTictsSub:
    def test_simple_sub(self, smallts):
        ts = smallts - smallts
        assert all(val == 0 for val in ts.values())

    def test_simple_sub_one_float(self, smallts):
        ts = smallts - 1
        assert list(ts.values()) == list(range(-1, 9))

    def test_sub_with_keys_differences_with_default(
        self, smallts_withdefault, otherts_withdefault
    ):
        ts = smallts_withdefault - otherts_withdefault
        assert ts[CURRENT + 1 * ONEHOUR] == 1 - 900
        assert ts[CURRENT + 2 * ONEHOUR] == 2 - 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 - 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 - 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 - 3000

    def test_sub_with_keys_differences_without_default(self, smallts, otherts):
        ts = smallts - otherts
        assert CURRENT + 1 * ONEHOUR not in ts.index
        assert ts[CURRENT + 2 * ONEHOUR] == 2 - 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 - 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 - 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 - 3000

    def test_sub_with_keys_differences_with_mixed_default_nodefault(
        self, smallts_withdefault, otherts
    ):
        ts = smallts_withdefault - otherts
        assert not ts._has_default
        assert CURRENT + 1 * ONEHOUR not in ts.index
        assert ts[CURRENT + 2 * ONEHOUR] == 2 - 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2 - 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 - 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 - 3000


class TestTictsMul:
    def test_simple_mul(self, smallts):
        ts = smallts * smallts
        assert list(ts.values()) == [val * val for val in smallts.values()]

    def test_simple_mul_one_float(self, smallts):
        ts = smallts * 1000.0
        assert list(ts.values()) == [val * 1000.0 for val in smallts.values()]


class TestTictsDiv:
    def test_simple_div(self, smallts):
        smallts[CURRENT] = 1  # can't divide by zero
        ts = smallts / smallts
        assert list(ts.values()) == [val / val for val in smallts.values()]

    def test_simple_div_with_default_to_zero(self, smallts):
        smallts.default = 0
        smallts[CURRENT] = 1  # can't divide by zero
        ts = smallts / smallts
        assert not ts._has_default

    def test_simple_div_one_float(self, smallts):
        ts = smallts / 1000.0
        assert list(ts.values()) == [val / 1000.0 for val in smallts.values()]


class TestTictsBoolean:
    def test_simple_le(self, smallts):
        result = smallts >= 5
        assert all(not val for val in result[CURRENT : CURRENT + 4 * ONEHOUR].values())
        assert all(
            val
            for val in result[CURRENT + 5 * ONEHOUR : CURRENT + 9 * ONEHOUR].values()
        )

    def test_simple_lt(self, smallts):
        result = smallts > 5
        assert all(not val for val in result[CURRENT : CURRENT + 5 * ONEHOUR].values())
        assert all(
            val
            for val in result[CURRENT + 6 * ONEHOUR : CURRENT + 9 * ONEHOUR].values()
        )

    def test_simple_eq(self, smallts):
        ts = smallts == smallts
        assert all(ts.values())


class TestTictsFloorCeil:
    def test_floor_on_float(self, smallts):
        ts = smallts.floor(2)
        assert all(value <= 2 for value in ts.values())

    def test_floor_on_ts(self, smallts_withdefault, otherts_withdefault):
        ts = smallts_withdefault.floor(otherts_withdefault)
        assert ts[CURRENT + 1 * ONEHOUR] == 1
        assert ts[CURRENT + 2 * ONEHOUR] == 2
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2
        assert ts[CURRENT + 3 * ONEHOUR] == 3
        assert ts[CURRENT + 4 * ONEHOUR] == 4

    def test_ceil_on_float(self, smallts):
        ts = smallts.ceil(7)
        assert all(value >= 7 for value in ts.values())

    def test_ceil_on_ts(self, smallts_withdefault, otherts_withdefault):
        ts = smallts_withdefault.ceil(otherts_withdefault)
        assert ts[CURRENT + ONEHOUR] == 900
        assert ts[CURRENT + 2 * ONEHOUR] == 1000
        assert ts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 3000

    def test_ceil_on_ts_check_changing_default(
        self, smallts_withdefault, otherts_withdefault
    ):
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
        self, smallts, emptyts, maskts
    ):
        with pytest.raises(ValueError) as err:
            smallts.mask_update(emptyts, maskts)
        assert "other is empty and has no default set" in str(err.value)

    def test_mask_update_with_empty_and_no_default_mask_raises(self, smallts, emptyts):
        with pytest.raises(ValueError) as err:
            smallts.mask_update(smallts, emptyts)
        assert "mask is empty and has no default set" in str(err.value)

    def test_simple_mask_update(self, smallts, otherts, maskts):
        smallts_keys = smallts.index
        otherts_keys = otherts.index
        smallts.mask_update(otherts, maskts)

        assert set(smallts.index) == set(smallts_keys).union(set(otherts_keys))

        assert smallts[CURRENT + 2 * ONEHOUR] == 2
        assert smallts[CURRENT + 2 * ONEHOUR + HALFHOUR] == 2000
        assert smallts[CURRENT + 3 * ONEHOUR] == 2000
        assert smallts[CURRENT + 4 * ONEHOUR] == 4

    def test_mask_update_with_other_being_empty_with_default(
        self, smallts, emptyts, maskts
    ):
        emptyts.default = -10.0
        smallts.mask_update(emptyts, maskts)

        assert smallts[CURRENT + 2 * ONEHOUR] == 2
        assert smallts[CURRENT + 3 * ONEHOUR] == -10.0
        assert smallts[CURRENT + 4 * ONEHOUR] == 4

    def test_mask_update_on_emptyts(self, smallts, emptyts, maskts):
        emptyts.mask_update(smallts, maskts)
        expected_ts = TimeSeries({CURRENT + 3 * ONEHOUR: 3})
        testing.assert_ts_equal(emptyts, expected_ts)


class TestSliceAssignment:
    """Test direct slice assignment with TimeSeries values."""

    def test_slice_assignment_overlays_values(self):
        """Slice assignment overlays values - keeps existing keys, only updates from other."""
        ts = TimeSeries(
            {
                CURRENT: 0,
                CURRENT + 1 * ONEHOUR: 1,
                CURRENT + 2 * ONEHOUR: 2,
                CURRENT + 3 * ONEHOUR: 3,
                CURRENT + 10 * ONEHOUR: 10,
            },
            default=100,
        )

        other = TimeSeries({CURRENT + 0.5 * ONEHOUR: 50}, default=100)

        ts[CURRENT : CURRENT + 3 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 0,
                    "2019-01-01T00:30:00+00:00": 50,
                    "2019-01-01T03:00:00+00:00": 3,
                    "2019-01-01T10:00:00+00:00": 10,
                },
                "default": 100,
                "name": "value",
            }
        )

    def test_slice_assignment_no_start_marker(self):
        """Slice assignment does NOT add start marker - only updates keys from other."""
        ts = TimeSeries({CURRENT: 0, CURRENT + 10 * ONEHOUR: 10}, default=5)
        other = TimeSeries({CURRENT + 2 * ONEHOUR: 100}, default=5)

        ts[CURRENT + 1 * ONEHOUR : CURRENT + 3 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 0,
                    "2019-01-01T02:00:00+00:00": 100,
                    "2019-01-01T03:00:00+00:00": 0,
                    "2019-01-01T10:00:00+00:00": 10,
                },
                "default": 5,
                "name": "value",
            }
        )

    def test_slice_assignment_adds_end_marker(self):
        """Slice assignment adds end marker to restore step function after the range."""
        ts = TimeSeries({CURRENT: 0, CURRENT + 10 * ONEHOUR: 10}, default=5)
        other = TimeSeries({CURRENT + 1 * ONEHOUR: 100}, default=5)

        ts[CURRENT : CURRENT + 3 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 0,
                    "2019-01-01T01:00:00+00:00": 100,
                    "2019-01-01T03:00:00+00:00": 0,
                    "2019-01-01T10:00:00+00:00": 10,
                },
                "default": 5,
                "name": "value",
            }
        )

    def test_slice_assignment_with_none_start(self):
        """ts[:end] = other should work (None start)."""
        ts = TimeSeries({CURRENT: 0, CURRENT + 10 * ONEHOUR: 10}, default=5)
        other = TimeSeries({CURRENT - 5 * ONEHOUR: 100}, default=5)

        ts[: CURRENT + 2 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2018-12-31T19:00:00+00:00": 100,
                    "2019-01-01T02:00:00+00:00": 0,
                    "2019-01-01T10:00:00+00:00": 10,
                },
                "default": 5,
                "name": "value",
            }
        )

    def test_slice_assignment_with_none_stop(self):
        """ts[start:] = other should work (None stop)."""
        ts = TimeSeries({CURRENT: 0, CURRENT + 10 * ONEHOUR: 10}, default=5)
        other = TimeSeries({CURRENT + 5 * ONEHOUR: 100}, default=5)

        ts[CURRENT + 2 * ONEHOUR :] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 0,
                    "2019-01-01T02:00:00+00:00": 5,  # default of other
                    "2019-01-01T05:00:00+00:00": 100,
                    "2019-01-01T10:00:00+00:00": 10,
                },
                "default": 5,
                "name": "value",
            }
        )

    def test_slice_assignment_with_both_none(self):
        """ts[:] = other overlays on entire series."""
        ts = TimeSeries({CURRENT: 0, CURRENT + 10 * ONEHOUR: 10}, default=5)
        other = TimeSeries({CURRENT + 5 * ONEHOUR: 100}, default=20)

        ts[:] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T05:00:00+00:00": 100,
                },
                "default": 20,
                "name": "value",
            }
        )

    def test_slice_assignment_empty_value_with_default(self):
        """Assigning empty TimeSeries just adds end marker."""
        ts = TimeSeries(
            {CURRENT: 0, CURRENT + 5 * ONEHOUR: 5, CURRENT + 10 * ONEHOUR: 10},
            default=100,
        )
        other = TimeSeries({}, default=50)

        ts[CURRENT + 2 * ONEHOUR : CURRENT + 8 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 0,
                    "2019-01-01T02:00:00+00:00": 50,
                    "2019-01-01T08:00:00+00:00": 5,
                    "2019-01-01T10:00:00+00:00": 10,
                },
                "default": 100,
                "name": "value",
            }
        )

    def test_slice_assignment_empty_value_no_default(self):
        """Assigning empty TimeSeries without default just adds end marker."""
        ts = TimeSeries(
            {CURRENT: 0, CURRENT + 5 * ONEHOUR: 5, CURRENT + 10 * ONEHOUR: 10},
            default=100,
        )
        other = TimeSeries({})

        ts[CURRENT + 2 * ONEHOUR : CURRENT + 8 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 0,
                    "2019-01-01T02:00:00+00:00": None,
                    "2019-01-01T08:00:00+00:00": 5,
                    "2019-01-01T10:00:00+00:00": 10,
                },
                "default": 100,
                "name": "value",
            }
        )

    def test_slice_assignment_without_self_default(self):
        """Slice assignment works without self default if end marker can be computed."""
        ts = TimeSeries({CURRENT: 0, CURRENT + 10 * ONEHOUR: 10})
        other = TimeSeries({CURRENT + 5 * ONEHOUR: 100}, default=5)

        ts[CURRENT + 2 * ONEHOUR : CURRENT + 8 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 0,
                    "2019-01-01T02:00:00+00:00": 5,
                    "2019-01-01T05:00:00+00:00": 100,
                    "2019-01-01T08:00:00+00:00": 0,
                    "2019-01-01T10:00:00+00:00": 10,
                },
                "default": "no_default",
                "name": "value",
            }
        )

    def test_slice_assignment_boundary_end_before_lower_bound(self):
        """Handle case where end < self.lower_bound."""
        ts = TimeSeries({CURRENT + 10 * ONEHOUR: 10}, default=5)
        other = TimeSeries({CURRENT: 100}, default=5)

        ts[CURRENT : CURRENT + 5 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 100,
                    "2019-01-01T05:00:00+00:00": 5,
                    "2019-01-01T10:00:00+00:00": 10,
                },
                "default": 5,
                "name": "value",
            }
        )

    def test_slice_assignment_on_empty_self(self):
        """Slice assignment on empty TimeSeries works with default for end marker."""
        ts = TimeSeries({}, default=5)
        other = TimeSeries({CURRENT: 100, CURRENT + 5 * ONEHOUR: 200}, default=10)

        ts[CURRENT : CURRENT + 10 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 100,
                    "2019-01-01T05:00:00+00:00": 200,
                    "2019-01-01T10:00:00+00:00": 5,
                },
                "default": 5,
                "name": "value",
            }
        )

    def test_slice_assignment_preserves_types(self):
        """Slice assignment preserves value types."""
        ts = TimeSeries({CURRENT: 1, CURRENT + 10 * ONEHOUR: 2}, default=1)
        other = TimeSeries({CURRENT + 2 * ONEHOUR: 100}, default=1)

        ts[CURRENT : CURRENT + 5 * ONEHOUR] = other

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 1,
                    "2019-01-01T02:00:00+00:00": 100,
                    "2019-01-01T05:00:00+00:00": 1,
                    "2019-01-01T10:00:00+00:00": 2,
                },
                "default": 1,
                "name": "value",
            }
        )

    def test_slice_assignment_with_operator(self):
        """Verify += operator works correctly."""
        ts = TimeSeries({}, default=1)
        ts[CURRENT] = 1
        ts[CURRENT + 10 * ONEHOUR] = 2
        ts[CURRENT : CURRENT + 2 * ONEHOUR] += 10

        assert ts.serialize("iso") == snapshot(
            {
                "data": {
                    "2019-01-01T00:00:00+00:00": 11,
                    "2019-01-01T02:00:00+00:00": 1,
                    "2019-01-01T10:00:00+00:00": 2,
                },
                "default": 1,
                "name": "value",
            }
        )
