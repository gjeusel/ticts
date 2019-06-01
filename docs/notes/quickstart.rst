QuickStart
==========

-------------
Instanciation
-------------

.. code:: python

    import ticts
    ticts.TimeSeries({'2019-01-01': 1, '2019-01-02': 2})
    ticts.TimeSeries({'2019-01-01': 1, '2019-01-02': 2}, default=0)

    import datetime
    dt1 = datetime.datetime(2019, 1, 1)
    ticts.TimeSeries({dt1: 1, '2019-01-02': 2})

    # from tuples
    ticts.TimeSeries(
      (dt1, 1),
      ('2019-01-02', 2)
    )


-------
Samples
-------

.. ipython:: python

    dt1
    onehour
    smallts
    otherts

-------
GetItem
-------

An **interval** is closed left, open right: **[ , [**

.. ipython:: python

   smallts.keys()

   # Accessing value at key
   smallts[dt1 + onehour]
   smallts[dt1]  # no default set
   otherts[dt1]  # default set

   # Accessing values sliced
   smallts[dt1: dt1 + 5 * onehour]  # calls TimeSeries.slice

   # Getting previous is the default
   key = dt1 + 2 * onehour
   smallts[key, 'previous'] == smallts[key] == 1

   # linear interpolation is available
   smallts[key, 'linear']

   # Get is still the one from dict
   smallts.get(key)


----------------------
Set Item, Set Interval
----------------------

.. ipython:: python

   ts = TimeSeries(smallts, default=0)
   ts[dt1 + onehour] = 2
   print(ts)

   start = dt1 + 4 * onehour
   end = dt2 + 7 * onehour
   ts.set_interval(start, end, 7)
   print(ts)

   # same as
   ts[start: end] = 7
   print(ts)


----------
Operations
----------

Sum

.. ipython:: python

   smallts + 10
   smallts + otherts
   sum([smallts, smallts, smallts])

Sub

.. ipython:: python

   smallts - otherts


Comparisons

.. ipython:: python

   smallts <= 10
   smallts <= otherts
   smallts < 10
   smallts < otherts

   smallts >= 10
   smallts > 10
