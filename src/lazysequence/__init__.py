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
from dataclasses import dataclass
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


@dataclass(frozen=True)
class _slice:  # noqa: N801
    start: Optional[int]
    stop: Optional[int]
    step: int

    @classmethod
    def fromslice(cls, aslice: slice) -> _slice:
        return cls(aslice.start, aslice.stop, aslice.step)

    def __init__(
        self, start: Optional[int], stop: Optional[int], step: Optional[int]
    ) -> None:
        if step == 0:
            raise ValueError("slice step cannot be zero")

        if step is None:
            step = 1

        object.__setattr__(self, "start", start)
        object.__setattr__(self, "stop", stop)
        object.__setattr__(self, "step", step)

    def hasnegativebounds(self) -> bool:
        return any(arg < 0 for arg in (self.start, self.stop) if arg is not None)

    def withpositivebounds(self, size: int) -> _slice:
        start, stop = self.start, self.stop

        if start is not None and start < 0:
            start = max(0, start + size)

        if stop is not None and stop < 0:
            stop = max(0, stop + size)

        return _slice(start, stop, self.step)

    def length(self, size: int) -> int:
        if self.stop is not None:
            size = min(size, self.stop)

        if self.start is not None:
            size = max(0, size - self.start)

        if size > 0:
            # This is equivalent to `math.ceil(result / step)`, but avoids
            # floating-point operations and importing `math`.
            size = 1 + (size - 1) // self.step

        return size

    def reverse(self, size: int) -> _slice:
        start, stop, step = self.start, self.stop, self.step

        step = -step

        if start is None:
            start = 0
        else:
            start = (size - 1) - start

        start = max(0, start)

        if stop is None:
            stop = size
        else:
            stop = (size - 1) - stop

        stop = max(0, stop)

        return _slice(start, stop, step)

    def astuple(self) -> tuple[Optional[int], Optional[int], int]:
        return self.start, self.stop, self.step

    def apply(self, iterable: Iterable[_T_co]) -> Iterator[_T_co]:
        return islice(iterable, *self.astuple())


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

        slice = _slice(start, stop, step)

        if slice.hasnegativebounds():
            self._fill()
            self._slice = slice.withpositivebounds(self._cachesize)
        else:
            self._slice = slice

    def _consume(self) -> Iterator[_T_co]:
        for item in self._iter:
            self._cache.append(item)
            yield item

    def _fill(self) -> None:
        self._cache.extend(self._iter)

    @property
    def _cachesize(self) -> int:
        return len(self._cache)

    def _iterate(self, iterator: Iterator[_T_co]) -> Iterator[_T_co]:
        if self._slice.step < 0:
            self._fill()

            slice = self._slice.reverse(self._cachesize)
            return slice.apply(reversed(self._cache))

        return self._slice.apply(chain(self._cache, iterator))

    def __iter__(self) -> Iterator[_T_co]:
        """Iterate over the items in the sequence."""
        return self._iterate(self._consume())

    def release(self) -> Iterator[_T_co]:
        """Iterate over the sequence without caching additional items.

        The sequence should no longer be used after calling this function. The
        same applies to slices of the sequence obtained by using ``s[i:j]``.

        Yields:
            The items in the sequence.
        """  # noqa: DAR201, DAR302
        return self._iterate(self._iter)

    def __bool__(self) -> bool:
        """Return True if there are any items in the sequence."""
        for _ in self:
            return True
        return False

    def __len__(self) -> int:
        """Return the number of items in the sequence."""
        self._fill()
        slice = self._slice

        if slice.step < 0:
            slice = slice.reverse(self._cachesize)

        return slice.length(self._cachesize)

    def _getslice(self, index: slice) -> lazysequence[_T_co]:
        slice = _slice.fromslice(index)
        if slice.hasnegativebounds():
            slice = slice.withpositivebounds(len(self))

        if slice.step < 0:
            return lazysequence(reversed(self[slice.start : slice.stop : -slice.step]))

        return lazysequence(slice.apply(self))

    def _getitem(self, index: int) -> _T_co:  # noqa: C901
        if index < 0:
            index += len(self)

        if index < 0:
            raise IndexError("lazysequence index out of range")

        start, stop, step = self._slice.astuple()
        index *= step

        if self._slice.step < 0:
            self._fill()
            if start is None:
                start = self._cachesize - 1
            else:
                start = min(start, self._cachesize - 1)

        if start is not None:
            index += start

        if index < 0:
            raise IndexError("lazysequence index out of range")

        if stop is not None and (
            step > 0 and index >= stop or step < 0 and index <= stop
        ):
            raise IndexError("lazysequence index out of range")

        try:
            return self._cache[index]
        except IndexError:
            pass

        index -= self._cachesize

        try:
            return next(islice(self._consume(), index, None))
        except StopIteration:
            raise IndexError("lazysequence index out of range") from None

    @overload
    def __getitem__(self, index: int) -> _T_co:
        """Return the item at the given index."""  # noqa: D418

    @overload
    def __getitem__(self, indices: slice) -> lazysequence[_T_co]:
        """Return a slice of the sequence."""  # noqa: D418

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[_T_co, lazysequence[_T_co]]:
        """Return the item at the given index."""
        return (
            self._getslice(index) if isinstance(index, slice) else self._getitem(index)
        )
