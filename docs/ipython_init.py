from datetime import timedelta

import arrow

from ticts import TimeSeries

onehour = timedelta(hours=1)
onemin = timedelta(minutes=1)
dt1 = arrow.get('2019-01-01')
dt2 = arrow.get('2019-01-02')

smalldct = {
    dt1 + onehour: 1,
    dt1 + 3 * onehour: 3,
    dt1 + 6 * onehour: 10,
}

smallts = TimeSeries(smalldct)

otherdct = {
    dt1 + 2 * onehour: 2,
    dt1 + 3 * onehour: 3,
    dt1 + 5 * onehour: 5,
}

otherts = TimeSeries(otherdct, default=0)
