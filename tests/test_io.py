import json

from ticts import TimeSeries, testing


class TestJSON:
    def test_serealize_iso(self, smallts):
        expected = {
            'data': {key.isoformat(): value
                     for key, value in smallts.items()},
            'default': 'no_default',
            'name': 'value'
        }
        assert expected == smallts.serealize(date_format='iso')

    def test_serealize_epoch(self, smallts):
        expected = {
            'data': {key.value: value
                     for key, value in smallts.items()},
            'default': 'no_default',
            'name': 'value'
        }
        assert expected == smallts.serealize()

    def test_to_json(self, smallts, tmpdir):
        path = tmpdir.join('test.json')
        smallts.to_json(path)
        expected = smallts.serealize()
        expected['data'] = {
            str(key): val
            for key, val in expected['data'].items()
        }
        returned = json.load(open(path, "r"))
        assert returned == expected

    def test_it_returns_timeseries_from_json(self, smallts, tmpdir):
        path = tmpdir.join('test.json')
        smallts.to_json(path)
        ts_read = TimeSeries.from_json(path)
        testing.assert_ts_equal(smallts, ts_read)
