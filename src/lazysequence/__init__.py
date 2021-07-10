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
from typing import Tuple
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

    def asslice(self) -> slice:
        return slice(*self.astuple())

    def hasnegativebounds(self) -> bool:
        return any(arg < 0 for arg in (self.start, self.stop) if arg is not None)

    def withpositivebounds(self, size: int) -> _slice:
        start, stop, step = self.astuple()

        if start is not None and start < 0:
            start = max(0, start + size)

        if stop is not None and stop < 0:
            stop += size
            if stop < 0:
                stop = None if step < 0 else 0

        return _slice(start, stop, step)

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
        assert self.step < 0  # noqa: S101

        start, stop, step = self.astuple()
        step = -step

        assert start is not None  # noqa: S101
        start = (size - 1) - start
        start = max(0, start)

        if stop is None:
            stop = size
        else:
            stop = (size - 1) - stop

        stop = max(0, stop)

        return _slice(start, stop, step)

    def astuple(self) -> Tuple[Optional[int], Optional[int], int]:
        return self.start, self.stop, self.step

    def apply(self, iterable: Iterable[_T_co]) -> Iterator[_T_co]:
        return islice(iterable, *self.astuple())

    def resolve(self, index: int) -> int:
        """Resolve index on a forward slice, where start <= stop and step > 0."""
        assert self.step > 0  # noqa: S101

        start, stop, step = self.astuple()

        if start is None:
            start = 0

        index = start + index * step

        if stop is not None and index >= stop:
            raise IndexError("lazysequence index out of range")

        return index

    def resolve_noraise(self, index: int) -> Optional[int]:
        """Resolve index, defaulting to the last valid slot."""
        assert self.step > 0  # noqa: S101

        try:
            return self.resolve(index)
        except IndexError:
            return self.stop - 1 if self.stop is not None else None

    def rresolve(self, index: int, size: int) -> int:
        """Resolve index on a backward slice, where start >= stop and step < 0."""
        assert self.step < 0  # noqa: S101

        start, stop, step = self.astuple()

        assert start is not None  # noqa: S101

        start = min(start, size - 1)
        index = start + index * step

        if index < 0 or stop is not None and index <= stop:
            raise IndexError("lazysequence index out of range")

        return index

    def rresolve_noraise(self, index: int, size: int) -> int:
        """Resolve index backwards, defaulting to the first valid slot."""
        try:
            return self.rresolve(index, size)
        except IndexError:
            return self.stop + 1 if self.stop is not None else 0


_defaultslice = slice(None)


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
        _cache: Optional[MutableSequence[_T_co]] = None,
        _indices: slice = _defaultslice,
    ) -> None:
        """Initialize."""
        self._iter = iter(iterable)
        self._cache = storage() if _cache is None else _cache

        slice = _slice.fromslice(_indices)

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
        slice = self._slice

        if slice.step < 0:
            self._fill()
            slice = slice.reverse(self._cachesize)
            return slice.apply(reversed(self._cache))

        return slice.apply(chain(self._cache, iterator))

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
        slice = self._slice

        self._fill()

        if slice.step < 0:
            slice = slice.reverse(self._cachesize)

        return slice.length(self._cachesize)

    def _getitem(self, index: int) -> _T_co:
        if index < 0:
            index += len(self)

        if index < 0:
            raise IndexError("lazysequence index out of range")

        if self._slice.step >= 0:
            index = self._slice.resolve(index)
        else:
            self._fill()
            index = self._slice.rresolve(index, self._cachesize)

        try:
            return self._cache[index]
        except IndexError:
            pass

        index -= self._cachesize

        try:
            return next(islice(self._consume(), index, None))
        except StopIteration:
            raise IndexError("lazysequence index out of range") from None

    def _getslice(self, indices: slice) -> lazysequence[_T_co]:  # noqa: C901
        def resolve(index: int) -> Optional[int]:
            if self._slice.step > 0:
                return self._slice.resolve_noraise(index)

            self._fill()
            return self._slice.rresolve_noraise(index, self._cachesize)

        def resolve_start(start: Optional[int], step: int) -> Optional[int]:
            assert start is None or start >= 0  # noqa: S101

            if start is None:
                start = 0 if step > 0 else len(self) - 1

            return resolve(start)

        def resolve_stop(stop: Optional[int], step: int) -> Optional[int]:
            assert stop is None or stop >= 0  # noqa: S101

            if stop is not None:
                return resolve(stop)

            if step > 0:
                return self._slice.stop

            if self._slice.start is None:
                return None

            if self._slice.step < 0:
                return self._slice.start + 1

            return self._slice.start - 1

        def resolve_slice(aslice: _slice) -> _slice:
            if aslice.hasnegativebounds():
                aslice = aslice.withpositivebounds(len(self))

            start, stop, step = aslice.astuple()

            start = resolve_start(start, step)
            stop = resolve_stop(stop, step)
            step *= self._slice.step

            return _slice(start, stop, step)

        theslice = resolve_slice(_slice.fromslice(indices))

        return lazysequence(self._iter, _cache=self._cache, _indices=theslice.asslice())

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
