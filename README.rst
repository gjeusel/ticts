.. |travis| image:: https://travis-ci.com/gjeusel/ticts.svg?branch=master
  :target: https://travis-ci.com/gjeusel/ticts
.. |readthedocs| image:: https://readthedocs.org/projects/ticts/badge/?version=latest
  :target: http://ticts.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status
.. |codecov| image:: https://codecov.io/gh/gjeusel/ticts/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/gjeusel/ticts
.. |pypi| image:: https://badge.fury.io/py/ticts.svg
  :target: https://pypi.python.org/pypi/ticts/
  :alt: Pypi package
.. |python| image:: https://img.shields.io/badge/python-3.6%2B-blue.svg
  :target: https://www.python.org/downloads/release/python-360/
  :alt: Python version 3.5+


===============================
ticts
===============================
|codecov| |travis| |python| |pypi|


A Python library for unevenly-spaced time series analysis.


Get Started `Notebook <https://mybinder.org/v2/gh/gjeusel/ticts/master?filepath=docs%2FTutorial.ipynb>`_.


Usage
-----

.. code:: python

   from ticts import TimeSeries
   ts = TimeSeries({
      '2019-01-01': 1,
      '2019-01-01 00:10:00': 2,
      '2019-01-01 00:11:00': 3,
   })
   assert ts['2019-01-01 00:05:00'] == 1

   ts['2019-01-01 00:04:00'] = 10
   assert ts['2019-01-01 00:05:00'] == 10

   assert ts + ts == 2 * ts

   from datetime import timedelta
   onemin = timedelta(minutes=1)
   ts.sample(freq=onemin)

   # if pandas installed:
   ts.to_dataframe()


Installation
------------

.. code:: bash

    pip install ticts
