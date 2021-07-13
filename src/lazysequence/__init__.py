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
from typing import Sized
from typing import Tuple
from typing import TypeVar
from typing import Union


_T_co = TypeVar("_T_co", covariant=True)


def _positive(index: int, size: int) -> int:
    """Convert a negative index to a non-negative integer.

    The index is interpreted relative to the position after the last item. If
    the index is smaller than ``-size``, IndexError is raised.
    """
    assert index < 0  # noqa: S101
    index += size

    if index < 0:
        raise IndexError("lazysequence index out of range")

    return index


def _positivestart(start: int, size: int) -> int:
    """Convert a negative start index to a non-negative integer.

    The index is interpreted relative to the position after the last item. If
    the index is smaller than ``-size``, zero is returned.
    """
    assert start < 0  # noqa: S101
    return max(0, start + size)


def _positivestop(stop: int, size: int, step: int) -> Optional[int]:
    """Convert a negative stop index to a non-negative integer.

    The index is interpreted relative to the position after the last item. If
    the index is smaller than ``-size``, the return value depends on ``step``.
    If ``step`` is positive, zero is returned. If ``step`` is negative, None is
    returned. Returning None for reverse slices ensures that an expression such
    as ``s[:-1000:-1]`` includes the first element of ``s``.
    """
    assert stop < 0  # noqa: S101

    stop += size
    if stop >= 0:
        return stop

    return 0 if step > 0 else None


@dataclass(frozen=True)
class _slice:  # noqa: N801
    """Slice representation.

    Attributes:
        start: The position of the first item, either None or a non-negative
            integer.
        stop: The position after the last item, either None or a non-negative
            integer.
        step: The distance between successive items, any integer except zero.
    """

    start: Optional[int]
    stop: Optional[int]
    step: int

    def __init__(
        self, start: Optional[int], stop: Optional[int], step: Optional[int]
    ) -> None:
        """Initialize."""
        if step == 0:
            raise ValueError("slice step cannot be zero")

        if step is None:
            step = 1

        object.__setattr__(self, "start", start)
        object.__setattr__(self, "stop", stop)
        object.__setattr__(self, "step", step)

    def astuple(self) -> Tuple[Optional[int], Optional[int], int]:
        """Return the attributes as a tuple."""
        return self.start, self.stop, self.step

    def apply(self, iterable: Iterable[_T_co], sized: Sized) -> Iterator[_T_co]:
        """Yield items from the iterable corresponding to this slice."""
        return islice(iterable, *self.astuple())

    def length(self, sized: Sized) -> int:
        """Return the number of items corresponding to this slice."""
        origin = self

        if origin.step < 0:
            origin = origin.reverse(sized)

        start, stop, step = origin.astuple()
        size = len(sized)

        if stop is not None:
            size = min(size, stop)

        if start is not None:
            size = max(0, size - start)

        if size > 0:
            # This is equivalent to `math.ceil(result / step)`, but avoids
            # floating-point operations and importing `math`.
            size = 1 + (size - 1) // abs(step)

        return size

    def reverse(self, sized: Sized) -> _slice:
        """Return the equivalent slice for a reversed sequence."""
        assert self.step < 0  # noqa: S101

        start, stop, step = self.astuple()
        size = len(sized)
        step = -step

        if start is None:
            start = size - 1

        start = (size - 1) - start
        start = max(0, start)

        if stop is None:
            stop = size
        else:
            stop = (size - 1) - stop

        stop = max(0, stop)

        return _slice(start, stop, step)

    def resolve(self, index: int, sized: Sized) -> int:
        """Return the equivalent index on the underlying sequence.

        In pseudo-code: ``s[slice][index] === s[slice.resolve(index)]``
        """
        if index < 0:
            index = _positive(index, self.length(sized))

        return self._resolve(index, sized, strict=True)

    def _resolve(self, index: int, sized: Sized, *, strict: bool = True) -> int:
        assert index >= 0  # noqa: S101
        return (
            self._resolveforward(index, sized, strict=strict)
            if self.step > 0
            else self._resolvebackward(index, sized, strict=strict)
        )

    def _resolveforward(self, index: int, sized: Sized, *, strict: bool = True) -> int:
        """Resolve index on a forward slice, where start <= stop and step > 0."""
        assert self.step > 0  # noqa: S101

        start, stop, step = self.astuple()

        if start is None:
            start = 0

        index = start + index * step

        if stop is not None and index >= stop:
            if strict:
                raise IndexError("lazysequence index out of range")

            # Default to the last valid slot.
            return max(0, stop - 1)

        return index

    def _resolvebackward(self, index: int, sized: Sized, *, strict: bool = True) -> int:
        """Resolve index on a backward slice, where start >= stop and step < 0."""
        assert self.step < 0  # noqa: S101

        size = len(sized)
        start, stop, step = self.astuple()

        if start is None:
            start = size - 1

        start = min(start, size - 1)
        index = start + index * step

        if index < 0 or stop is not None and index <= stop:
            if strict:
                raise IndexError("lazysequence index out of range")

            # Default to the first valid slot.
            return stop + 1 if stop is not None else 0

        return index

    def resolveslice(self, slice: _slice, sized: Sized) -> _slice:
        """Return the equivalent slice on the underlying sequence.

        In pseudo-code: ``s[slice0][slice1] === s[slice0.resolve(slice1)]``
        """
        start, stop, step = slice.astuple()

        start = self._resolvestart(start, step, sized)
        stop = self._resolvestop(stop, step, sized)
        step *= self.step

        return _slice(start, stop, step)

    def _resolvestart(
        self, start: Optional[int], step: int, sized: Sized
    ) -> Optional[int]:
        if start is not None and start < 0:
            start = _positivestart(start, self.length(sized))

        if start is not None:
            return self._resolve(start, sized, strict=False)

        if step > 0:
            return self.start

        if self.stop is None:
            return None

        return self.stop + 1 if self.step < 0 else self.stop - 1

    def _resolvestop(
        self, stop: Optional[int], step: int, sized: Sized
    ) -> Optional[int]:
        if stop is not None and stop < 0:
            stop = _positivestop(stop, self.length(sized), step)

        if stop is not None:
            return self._resolve(stop, sized, strict=False)

        if step > 0:
            return self.stop

        if self.start is None:
            return None

        return self.start + 1 if self.step < 0 else self.start - 1


_defaultslice = _slice(None, None, None)


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
        _slice: _slice = _defaultslice,
    ) -> None:
        """Initialize."""
        parent = self

        class _Total(Sized):
            def __len__(self) -> int:
                parent._fill()
                return len(parent._cache)

        self._iter = iter(iterable)
        self._cache = storage() if _cache is None else _cache
        self._slice = _slice
        self._total = _Total()

    def _consume(self) -> Iterator[_T_co]:
        """Yield from the iterator, adding each item to the cache."""
        for item in self._iter:
            self._cache.append(item)
            yield item

    def _fill(self) -> None:
        """Add all items from the iterator to the cache."""
        self._cache.extend(self._iter)

    def _iterate(self, iterator: Iterator[_T_co]) -> Iterator[_T_co]:
        """Iterate over the items in the sequence."""
        slice = self._slice

        if slice.step > 0:
            iterator = chain(self._cache, iterator)
        else:
            slice = slice.reverse(self._total)

            self._fill()
            iterator = reversed(self._cache)

        return slice.apply(iterator, self._total)

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
        return self._slice.length(self._total)

    def _getitem(self, index: int) -> _T_co:
        """Return the item at the given index."""
        index = self._slice.resolve(index, self._total)

        try:
            return self._cache[index]
        except IndexError:
            pass

        index -= len(self._cache)

        try:
            return next(islice(self._consume(), index, None))
        except StopIteration:
            raise IndexError("lazysequence index out of range") from None

    def _getslice(self, indices: slice) -> lazysequence[_T_co]:  # noqa: C901
        """Return a slice of the sequence."""
        slice = _slice(indices.start, indices.stop, indices.step)
        slice = self._slice.resolveslice(slice, self._total)

        return lazysequence(self._iter, _cache=self._cache, _slice=slice)

    @overload
    def __getitem__(self, index: int) -> _T_co:
        """Return the item at the given index."""  # noqa: D418

    @overload
    def __getitem__(self, indices: slice) -> lazysequence[_T_co]:
        """Return a slice of the sequence."""  # noqa: D418

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[_T_co, lazysequence[_T_co]]:
        """Return the item at the given index, or a slice of the sequence."""
        return (
            self._getslice(index) if isinstance(index, slice) else self._getitem(index)
        )
