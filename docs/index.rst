:github_url: https://github.com/gjeusel/ticts

Welcome to ticts's documentation!
=================================

A Python library for unevenly-spaced time series analysis.

.. image:: _static/img/example.png
   :scale: 40%

Notebooks to play around are available `here <https://mybinder.org/v2/gh/gjeusel/ticts/master?filepath=docs%2FTutorial.ipynb>`_.

Why ?
-----
Sensors become omnipresents, and often the measurements are done at irregural time intervals.
I found it hard to work with using pandas, and found myself always swithing back to the evenly-spaced
timeseries world, by resampling at the lowest frequency applying a fill forward.
This is definitely not how it should works ! And you loose information.

About TicTs
-----------

The purpose is to provide a simple and intuitive interface to manipulate this kind of data, including:

   - operations (sum, sub, mul, div, max, min)
   - setting intervals
   - methods to pass from evenly-spaced to unevenly-spaced and vice-versa

You have to keep in mind the following rules:

   - intervals are open left, closed right
   - timestamp are always localized, defaulting to UTC
   - setting a default value to your timeseries might be important

.. toctree::
   :maxdepth: 2
   :caption: Notes

   quickstart <notes/quickstart>


.. toctree::
   :maxdepth: 2
   :caption: Package Reference

   ticts.timeseries <src/timeseries>


.. toctree::
   :maxdepth: 1
   :caption: Miscellaneous

   authors
   changelog

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
