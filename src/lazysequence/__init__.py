"""Lazy sequences.

>>> from lazysequence import lazysequence
>>>
>>> def load_records():
...     yield from [1, 2, 3, 4, 5, 6]  # pretend each iteration is expensive
...
>>> records = lazysequence(load_records())
>>> if not records:
...     raise SystemExit("no records found")
...
>>> first, second = records[:2]
>>>
>>> print("The first record is", first)
The first record is 1
>>> print("The second record is", second)
The second record is 2
>>>
>>> for record in records.release():  # do not cache all records in memory
...     print("record", record)
...
record 1
record 2
record 3
record 4
record 5
record 6
"""
from collections import deque
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import MutableSequence
from typing import overload
from typing import Sequence
from typing import TypeVar
from typing import Union


_T_co = TypeVar("_T_co", covariant=True)


class _LazySequence(Sequence[_T_co]):
    """A lazy sequence provides sequence operations on an iterable."""

    def __init__(
        self,
        iterable: Iterable[_T_co],
        *,
        storage: Callable[[], MutableSequence[_T_co]] = deque
    ) -> None:
        """Initialize."""
        self._iter = iter(iterable)
        self._cache: MutableSequence[_T_co] = storage()

    def _consume(self) -> Iterator[_T_co]:
        for item in self._iter:
            self._cache.append(item)
            yield item

    def __iter__(self) -> Iterator[_T_co]:
        """Iterate over the items in the sequence."""
        yield from self._cache
        yield from self._consume()

    def release(self) -> Iterator[_T_co]:
        """Iterate over the sequence without caching additional items.

        The sequence should no longer be used after calling this function.
        """
        yield from self._cache
        yield from self._iter

    def __bool__(self) -> bool:
        """Return True if there are any items in the sequence."""
        for _ in self:
            return True
        return False

    def __len__(self) -> int:
        """Return the number of items in the sequence."""
        return len(self._cache) + sum(1 for _ in self._consume())

    @overload
    def __getitem__(self, index: int) -> _T_co:
        """Return the item at the given index."""  # noqa: D418

    @overload
    def __getitem__(self, indices: slice) -> Sequence[_T_co]:
        """Return a slice of the sequence."""  # noqa: D418

    def __getitem__(self, index: Union[int, slice]) -> Union[_T_co, Sequence[_T_co]]:
        """Return the item at the given index."""
        if isinstance(index, slice):
            return _LazySequence(
                self[position] for position in range(*index.indices(len(self)))
            )

        if index < 0:
            index += len(self)

        try:
            return self._cache[index]
        except IndexError:
            pass

        index -= len(self._cache)

        for position, item in enumerate(self._consume()):
            if index == position:
                return item

        raise IndexError("lazysequence index out of range")


lazysequence = _LazySequence
