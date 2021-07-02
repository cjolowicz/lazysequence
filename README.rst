lazysequence
============

|PyPI| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

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


**tl;dr** A lazy sequence makes an iterator look like a tuple.

.. code:: python

   from lazysequence import LazySequence

   def load_records():
       yield from [1, 2, 3, 4, 5, 6]  # pretend each iteration is expensive

   records = LazySequence(load_records())
   if not records:
       raise SystemExit("no records found")

   first, second = records[:2]

   print("The first record is", first)
   print("The second record is", second)

   for record in records.release():  # do not cache all records in memory
       print("record", record)


Sometimes you need to peek ahead at items returned by an iterator. How do you do that?

If the iterator does not need to be used later, just consume the items from the iterator. If later code needs to see all the items from the iterator, there are various options:

1. You could pass the consumed items to the surrounding code separately. This can get messy, though.
2. You could copy the items into a sequence beforehand. This is an option if the copy does not take a lot of space or time.
3. You could duplicate the iterator using `itertools.tee`_, or write your own custom itertool. Consumed items are buffered internally. There are some good examples of this approach on SO, by `Alex Martelli`_, `Raymond Hettinger`_, and `Ned Batchelder`_.

.. _itertools.tee: https://docs.python.org/3/library/itertools.html#itertools.tee
.. _Alex Martelli: https://stackoverflow.com/a/1518097/1355754
.. _Raymond Hettinger: https://stackoverflow.com/a/15726344/1355754
.. _Ned Batchelder: https://stackoverflow.com/a/1517965/1355754

A lazy sequence combines advantages from option 2 and option 3. It is constructed from an iterable, and implements `collections.abc.Sequence`_, providing the full set of immutable sequence operations on the iterable. Consumed items are cached internally, so the lookahead can happen transparently, and remains invisible to later code. Unlike a full copy (option 2), but like a duplicated iterator (option 3), items are only consumed and stored in memory as far as required for any given operation.

.. _collections.abc.Sequence: https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence

**Caveats:**

- The lazy sequence will eventually store all items in memory. If this is a problem, use ``s.release()`` to obtain an iterator over the sequence items without further caching. After calling this function, the sequence should no longer be used.
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
