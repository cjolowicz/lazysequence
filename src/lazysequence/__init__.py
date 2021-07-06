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
    step: Optional[int]

    def __init__(
        self, start: Optional[int], stop: Optional[int], step: Optional[int]
    ) -> None:
        if step == 0:
            raise ValueError("slice step cannot be zero")

        object.__setattr__(self, "start", start)
        object.__setattr__(self, "stop", stop)
        object.__setattr__(self, "step", step)

    def isnegative(self) -> bool:
        return any(arg < 0 for arg in (self.start, self.stop) if arg is not None)

    def aspositive(self, size: int) -> _slice:
        start, stop = self.start, self.stop

        if start is not None and start < 0:
            start = max(0, start + size)

        if stop is not None and stop < 0:
            stop = max(0, stop + size)

        return _slice(start, stop, self.step)

    def reverse(self, size: int) -> _slice:
        start, stop, step = self.start, self.stop, self.step

        if step is None:
            step = 1  # pragma: no cover

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

    def astuple(self) -> tuple[Optional[int], Optional[int], Optional[int]]:
        return self.start, self.stop, self.step


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

        theslice = _slice(start, stop, step)

        if theslice.isnegative():
            theslice = theslice.aspositive(self._unboundedsize)

        self._slice = theslice

    @property
    def _start(self) -> Optional[int]:
        value: Optional[int] = self._slice.start
        return value

    @property
    def _stop(self) -> Optional[int]:
        value: Optional[int] = self._slice.stop
        return value

    @property
    def _step(self) -> Optional[int]:
        value: Optional[int] = self._slice.step
        return value

    def _consume(self) -> Iterator[_T_co]:
        for item in self._iter:
            self._cache.append(item)
            yield item

    @property
    def _unboundedsize(self) -> int:
        return len(self._cache) + sum(1 for _ in self._consume())

    def __iter__(self) -> Iterator[_T_co]:
        """Iterate over the items in the sequence."""
        if self._step is not None and self._step < 0:
            size = self._unboundedsize  # fills self._cache

            theslice = self._slice.reverse(size)
            return islice(reversed(self._cache), *theslice.astuple())

        return islice(chain(self._cache, self._consume()), *self._slice.astuple())

    def release(self) -> Iterator[_T_co]:
        """Iterate over the sequence without caching additional items.

        The sequence should no longer be used after calling this function. The
        same applies to slices of the sequence obtained by using ``s[i:j]``.

        Yields:
            The items in the sequence.
        """  # noqa: DAR201, DAR302
        if self._step is not None and self._step < 0:
            size = self._unboundedsize  # fills self._cache

            theslice = self._slice.reverse(size)
            return islice(reversed(self._cache), *theslice.astuple())

        return islice(chain(self._cache, self._iter), *self._slice.astuple())

    def __bool__(self) -> bool:
        """Return True if there are any items in the sequence."""
        for _ in self:
            return True
        return False

    def __len__(self) -> int:
        """Return the number of items in the sequence."""
        size = self._unboundedsize
        start, stop, step = self._slice.astuple()

        if step is not None and step < 0:
            theslice = self._slice.reverse(size)
            start, stop, step = theslice.astuple()

        result = size

        if stop is not None:
            result = min(result, stop)

        if start is not None:
            result = max(0, result - start)

        if step is not None and result > 0:
            # This is equivalent to `math.ceil(result / step)`, but avoids
            # floating-point operations and importing `math`.
            result = 1 + (result - 1) // step

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
        start: Optional[int]
        stop: Optional[int]
        step: Optional[int]

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

        start, stop, step = self._start, self._stop, self._step
        if step is None:
            step = 1
        else:
            if step < 0:
                size = self._unboundedsize
                if start is None:
                    start = size - 1
                else:
                    start = min(start, size - 1)

            index *= step

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

        index -= len(self._cache)

        try:
            return next(islice(self._consume(), index, None))
        except StopIteration:
            raise IndexError("lazysequence index out of range") from None
