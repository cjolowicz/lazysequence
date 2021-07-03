lazysequence
============

|PyPI| |Python Version| |License| |Read the Docs| |Tests| |Codecov|

.. |PyPI| image:: https://img.shields.io/pypi/v/lazysequence.svg
   :target: https://pypi.org/project/lazysequence/
   :alt: PyPI
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/lazysequence
   :target: https://pypi.org/project/lazysequence
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/lazysequence
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/lazysequence/latest.svg?label=Read%20the%20Docs
   :target: https://lazysequence.readthedocs.io/
   :alt: Read the documentation at https://lazysequence.readthedocs.io/
.. |Tests| image:: https://github.com/cjolowicz/lazysequence/workflows/Tests/badge.svg
   :target: https://github.com/cjolowicz/lazysequence/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/cjolowicz/lazysequence/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/cjolowicz/lazysequence
   :alt: Codecov


A lazy sequence makes an iterator look like an immutable sequence:

.. code:: python

   from lazysequence import lazysequence

   def load_records():
       return range(10)  # let's pretend this is expensive

   records = lazysequence(load_records())
   if not records:
       raise SystemExit("no records found")

   first, second = records[:2]

   print("The first record is", first)
   print("The second record is", second)

   for record in records.release():  # do not cache all records in memory
       print("record", record)


Why?
----

Sometimes you need to peek ahead at items returned by an iterator. But what if later code needs to see all the items from the iterator? Then you have some options:

1. Pass any consumed items separately. This can get messy, though.
2. Copy the iterator into a sequence beforehand, if that does not take a lot of space or time.
3. Duplicate the iterator using `itertools.tee`_, or write your own custom itertool that buffers consumed items internally. There are some good examples of this approach on SO, by `Alex Martelli`_, `Raymond Hettinger`_, and `Ned Batchelder`_.

.. _itertools.tee: https://docs.python.org/3/library/itertools.html#itertools.tee
.. _Alex Martelli: https://stackoverflow.com/a/1518097/1355754
.. _Raymond Hettinger: https://stackoverflow.com/a/15726344/1355754
.. _Ned Batchelder: https://stackoverflow.com/a/1517965/1355754

A lazy sequence combines advantages from option 2 and option 3. It is an immutable sequence that wraps the iterable and caches consumed items in an internal buffer. By implementing `collections.abc.Sequence`_, lazy sequences provide the full set of sequence operations on the iterable. Unlike a copy (option 2), but like a duplicate (option 3), items are only consumed and stored in memory as far as required for any given operation.

.. _collections.abc.Sequence: https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence

There are some caveats:

- The lazy sequence will eventually store all items in memory. If this is a problem, use ``s.release()`` to obtain an iterator over the sequence items without further caching. After calling this function, the sequence should no longer be used.
- Slicing returns a new lazy sequence with a reference to the old lazy sequence. Don't do this in a tight loop.
- Explicit is better than implicit. Clients may be better off being passed an iterator and dealing with its limitations. For example, clients may not expect ``len(s)`` to incur the cost of consuming the iterator to its end.


Installation
------------

You can install *lazysequence* via pip_ from PyPI_:

.. code:: console

   $ pip install lazysequence


Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


License
-------

Distributed under the terms of the `MIT license`_,
*lazysequence* is free and open source software.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------

This project was generated from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.

.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _MIT license: https://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _file an issue: https://github.com/cjolowicz/lazysequence/issues
.. _pip: https://pip.pypa.io/
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Usage: https://lazysequence.readthedocs.io/en/latest/usage.html
