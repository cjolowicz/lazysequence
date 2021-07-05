"""Lazy sequences.

>>> from lazysequence import lazysequence
>>>
>>> def load_records():
...     return range(10)  # let's pretend this is expensive
...
>>> records = lazysequence(load_records())
>>> if not records:
...     raise SystemExit("no records found")
...
>>> first, second = records[:2]
>>>
>>> print("The first record is", first)
The first record is 0
>>> print("The second record is", second)
The second record is 1
>>>
>>> for record in records.release():  # do not cache all records in memory
...     print("record", record)
...
record 0
record 1
record 2
record 3
record 4
record 5
record 6
record 7
record 8
record 9
"""
from __future__ import annotations

from collections import deque
from itertools import chain
from itertools import islice
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import MutableSequence
from typing import Optional
from typing import overload
from typing import Sequence
from typing import TypeVar
from typing import Union


_T_co = TypeVar("_T_co", covariant=True)


class lazysequence(Sequence[_T_co]):  # noqa: N801
    """A lazy sequence provides sequence operations on an iterable.

    Args:
        iterable: The iterable being wrapped.
        storage: A class or callable used to create the internal cache for
            items consumed from the iterator. By default, ``collections.deque``
            is used.
    """

    def __init__(
        self,
        iterable: Iterable[_T_co],
        *,
        storage: Callable[[], MutableSequence[_T_co]] = deque,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        step: Optional[int] = None,
    ) -> None:
        """Initialize."""
        self._iter = iter(iterable)
        self._cache: MutableSequence[_T_co] = storage()

        if any(arg < 0 for arg in (start, stop) if arg is not None):
            size = sum(1 for _ in self._consume())

            if start is not None and start < 0:
                start = max(0, start + size)

            if stop is not None and stop < 0:
                stop = max(0, stop + size)

        if step == 0:
            raise ValueError("slice step cannot be zero")

        self._start = start
        self._stop = stop
        self._step = step

    def _consume(self) -> Iterator[_T_co]:
        for item in self._iter:
            self._cache.append(item)
            yield item

    def __iter__(self) -> Iterator[_T_co]:
        """Iterate over the items in the sequence."""
        if self._step is not None and self._step < 0:
            for _ in self._consume():
                pass

            return islice(
                reversed(self._cache),
                self._start,
                self._stop,
                -self._step,
            )

        return islice(
            chain(self._cache, self._consume()), self._start, self._stop, self._step
        )

    def release(self) -> Iterator[_T_co]:
        """Iterate over the sequence without caching additional items.

        The sequence should no longer be used after calling this function. The
        same applies to slices of the sequence obtained by using ``s[i:j]``.

        Yields:
            The items in the sequence.
        """  # noqa: DAR201, DAR302
        return islice(
            chain(self._cache, self._iter), self._start, self._stop, self._step
        )

    def __bool__(self) -> bool:
        """Return True if there are any items in the sequence."""
        for _ in self:
            return True
        return False

    def __len__(self) -> int:
        """Return the number of items in the sequence."""
        result = len(self._cache) + sum(1 for _ in self._consume())

        if self._stop is not None:
            result = min(result, self._stop)

        if self._start is not None:
            result = max(0, result - self._start)

        if self._step is not None and result > 0:
            # This is equivalent to `math.ceil(result / self._step)`, but avoids
            # floating-point operations and importing `math`.
            result = 1 + (result - 1) // self._step

        return result

    @overload
    def __getitem__(self, index: int) -> _T_co:
        """Return the item at the given index."""  # noqa: D418

    @overload
    def __getitem__(self, indices: slice) -> lazysequence[_T_co]:
        """Return a slice of the sequence."""  # noqa: D418

    def __getitem__(  # noqa: C901
        self, index: Union[int, slice]
    ) -> Union[_T_co, lazysequence[_T_co]]:
        """Return the item at the given index."""
        if isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step

            if step is not None and step < 0:
                return lazysequence(reversed(self[start:stop:-step]))

            if start is not None and start < 0:
                start = max(0, start + len(self))

            if stop is not None and stop < 0:
                stop = max(0, stop + len(self))

            return lazysequence(islice(self, start, stop, step))

        if index < 0:
            index += len(self)

        if index < 0:
            raise IndexError("lazysequence index out of range")

        if self._step is not None:
            index *= self._step

        if self._start is not None:
            index += self._start

        if self._stop is not None and index >= self._stop:
            raise IndexError("lazysequence index out of range")

        try:
            return self._cache[index]
        except IndexError:
            pass

        index -= len(self._cache)

        try:
            return next(islice(self._consume(), index, None))
        except StopIteration:
            raise IndexError("lazysequence index out of range") from None
