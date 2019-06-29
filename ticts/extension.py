import pandas as pd


def to_dataframe(self):
    return pd.DataFrame(data={"value": self.values()}, index=self.keys())


def sample_period(self, sampling_period=None, start=None, end=None, idx=None, operation="mean"):
    """Sampling on intervals by using some operation (mean, max or min).

    It can be called either with sampling_period, start, end
    or with a idx as a DateTimeIndex.

    The returing pd.Series will be indexed either on
    pd.date_range(start, end, freq=sampling_period) or on idx.

    :param sampling_period: the sampling period
    :param start: the start time of the sampling
    :param end: the end time of the sampling
    :param idx: a DateTimeIndex with the start times of the intervals
    :param operation: "mean", "max" or "min"
    :return: a pandas Series with the Trace sampled
    """

    if idx is None:
        # create index on [start, end)
        idx = pd.date_range(start or self.lower_bound, end or self.upper_bound, freq=sampling_period, closed=None)

    start, end = idx[0], idx[-1]

    idx_list = idx.values  # list(idx)

    # create all inflexion points
    def items_in_horizon():
        # yields all items between start and end as well as start and end
        yield (start, self[start])
        for t, v in self.items():
            if t <= start:
                continue
            if t >= end:
                break
            yield t, v
        yield (end, self[end])

    inflexion_times, inflexion_values = zip(*items_in_horizon())
    inflexion_times = pd.DatetimeIndex(inflexion_times)

    # identify all inflexion intervals
    # by index: point i is in interval [idx[ifl_int[i]], idx[ifl_int[i]+1]
    # TODO: look to use searchsorted as it operates more efficienly (but offset of 1 in most cases)
    inflexion_intervals = inflexion_times.map(lambda t: idx.get_loc(t, method="ffill"))

    # convert DatetimeIndex to numpy array for faster indexation
    inflexion_times_tz = inflexion_times.tz
    inflexion_times = inflexion_times.values

    Np1 = len(idx_list) - 1

    # convert to timestamp
    # (to make interval arithmetic faster, no need for total_seconds)
    inflexion_times = inflexion_times.astype("int64")
    idx_times = idx.astype("int64")

    # initialise init, update and finish functions depending
    # on the aggregation operator
    init, update, finish = {
        "mean": (
            lambda t, v: v * 0,
            lambda agg, t0, t1, v: agg + (t1 - t0) * v,
            lambda agg, t_start, t_end: agg / (t_end - t_start),
        ),
        "max": (lambda t, v: v, lambda agg, t0, t1, v: max(agg, v), lambda agg, t_start, t_end: agg),
        "min": (lambda t, v: v, lambda agg, t0, t1, v: min(agg, v), lambda agg, t_start, t_end: agg),
    }[operation]

    # initialise first interval
    t_start, t_end = idx_times[:2]
    i0, t0, v0 = 0, t_start, self[start]
    agg = init(t0, v0)

    result = []
    for i1, t1, v1 in zip(inflexion_intervals, inflexion_times, inflexion_values):
        if i0 != i1:
            # change of interval

            # finish previous interval
            agg = update(agg, t0, t_end, v0)
            agg = finish(agg, t_start, t_end)
            result.append((idx_list[i0], agg))

            # handle all intervals between t_end and t1
            if i1 != i0 + 1:
                result.append((idx_list[i0 + 1], v0))

            # if last_point, break
            if i1 == Np1:
                break

            # set up new interval
            t_start, t_end = idx_times[i1 : i1 + 2]
            i0, t0, v0 = i1, t_start, v1
            agg = init(t0, v0)

        agg = update(agg, t0, t1, v0)

        i0, t0, v0 = i1, t1, v1

    # convert to Series
    sr = pd.Series(data=[v for _, v in result], index=pd.DatetimeIndex([ts for ts, _ in result], tz=inflexion_times_tz))

    # reindex and fill in the blanks
    sr = sr.reindex(idx[:-1]).ffill()

    return sr
