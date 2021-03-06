"""Unit tests for lazysequence."""
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

import pytest

from lazysequence import lazysequence


def test_init() -> None:
    """It is created from an iterable."""
    lazysequence([])


def test_len() -> None:
    """It returns the number of items."""
    s: lazysequence[int] = lazysequence([])
    assert 0 == len(s)


def test_getitem() -> None:
    """It returns the item at the given position."""
    s = lazysequence([1])
    assert 1 == s[0]


def test_getitem_second() -> None:
    """It returns the item at the given position."""
    s = lazysequence([1, 2])
    assert 2 == s[1]


def test_getitem_negative() -> None:
    """It returns the item at the given position."""
    s = lazysequence([1, 2])
    assert 2 == s[-1]


def test_getitem_past_cache() -> None:
    """It returns the item at the given position."""
    s = lazysequence([1, 2])
    assert (1, 2) == (s[0], s[1])


def test_getslice() -> None:
    """It returns the items at the given positions."""
    s = lazysequence([1, 2])
    [item] = s[1:]
    assert 2 == item


def test_getslice_negative_start() -> None:
    """It returns the items at the given positions."""
    s = lazysequence([1, 2])
    [item] = s[-1:]
    assert 2 == item


def test_getslice_negative_start_empty() -> None:
    """It returns the items at the given positions."""
    s: lazysequence[int] = lazysequence([])
    for _ in s[-1:]:
        pass


def test_getslice_negative_stop() -> None:
    """It returns the items at the given positions."""
    s = lazysequence([1, 2])
    [item] = s[:-1]
    assert 1 == item


def test_getslice_negative_stop_empty() -> None:
    """It returns the items at the given positions."""
    s: lazysequence[int] = lazysequence([])
    for _ in s[:-1]:
        pass


def test_getslice_negative_step() -> None:
    """It returns the items at the given positions."""
    s = lazysequence([1, 2])
    a, b = s[::-1]
    assert (2, 1) == (a, b)


def test_getslice_negative_step_and_start() -> None:
    """It returns the items at the given positions."""
    s = lazysequence([1, 2, 3])
    a, b, c = s[3::-1]
    assert (3, 2, 1) == (a, b, c)


def test_getslice_negative_step_and_stop() -> None:
    """It returns the items at the given positions."""
    s = lazysequence([1, 2, 3])
    [a] = s[:1:-1]
    assert 3 == a


def test_outofrange() -> None:
    """It raises IndexError."""
    s: lazysequence[int] = lazysequence([])
    with pytest.raises(IndexError):
        s[0]


def test_outofrange_negative() -> None:
    """It raises IndexError."""
    s = lazysequence([1, 2])
    with pytest.raises(IndexError):
        s[-3]


def test_bool_false() -> None:
    """It is False for an empty sequence."""
    s: lazysequence[int] = lazysequence([])
    assert not s


def test_bool_true() -> None:
    """It is False for a non-empty sequence."""
    s = lazysequence([1])
    assert s


def test_release() -> None:
    """It iterates over the items in the sequence."""
    s = lazysequence([1, 2, 3])
    a, b, c = s.release()
    assert (1, 2, 3) == (a, b, c)


def test_paging() -> None:
    """It can be used to obtain successive slices."""
    s = lazysequence(range(10000))
    while s:
        s = s[10:]
    assert not s


def test_slice_with_zero_step() -> None:
    """It raises an exception."""
    s = lazysequence(range(10))
    with pytest.raises(ValueError, match="slice step cannot be zero"):
        s[::0]


SLICE_EXAMPLE_PARAMS = ("size", "start", "stop", "step")
SLICE_EXAMPLES = [
    (0, None, -1, None),
    (0, None, 0, None),
    (0, None, 1, None),
    (0, -1, None, None),
    (0, 8, 4, -3),
    (1, None, -1, None),
    (1, None, 0, None),
    (1, None, 1, None),
    (1, -1, None, None),
    (2, None, -3, None),
    (2, None, -2, None),
    (2, None, -1, None),
    (2, None, 1, None),
    (3, 2, 0, -1),
    (10, None, None, -100),
    (10, None, None, -11),
    (10, None, None, -10),
    (10, None, None, -9),
    (10, None, None, -8),
    (10, None, None, -7),
    (10, None, None, -6),
    (10, None, None, -5),
    (10, None, None, -4),
    (10, None, None, -3),
    (10, None, None, -2),
    (10, None, None, -2),
    (10, None, None, -1),
    (10, None, None, 1),
    (10, None, None, 2),
    (10, None, None, 2),
    (10, None, None, 3),
    (10, None, None, 4),
    (10, None, None, 5),
    (10, None, None, 6),
    (10, None, None, 7),
    (10, None, None, 8),
    (10, None, None, 9),
    (10, None, None, 9),
    (10, None, None, 10),
    (10, None, None, 10),
    (10, None, None, 11),
    (10, None, None, 11),
    (10, None, None, 100),
    (10, None, -11, -1),
    (10, -5, -1, None),
    (10, -5, 9, None),
    (10, -1, -5, None),
    (10, -1, 5, None),
    (10, 0, 10, 1),
    (10, 3, 0, -2),
    (10, 3, 0, 2),
    (10, 3, 6, -2),
    (10, 3, 6, 2),
    (10, 5, -1, None),
    (10, 5, 9, None),
    (10, 6, 3, -2),
    (10, 8, 4, -3),
    (10, 9, -5, None),
    (10, 9, 0, -1),
    (10, 9, 5, None),
    (10, 9, 8, -1),
    (10, 10, 0, -1),
    (100, None, -1000, None),
    (100, None, -10, None),
    (100, None, 10, None),
    (100, None, 1000, None),
    (100, -1000, None, None),
    (100, -10, None, None),
    (100, 10, None, None),
    (100, 100, None, None),
    (100, 1000, None, None),
]

SLICE_EXAMPLES_GETITEM = [
    (3, 2, 0, -1),
    (10, None, None, -100),
    (10, None, None, -11),
    (10, None, None, -10),
    (10, None, None, -9),
    (10, None, None, -8),
    (10, None, None, -7),
    (10, None, None, -6),
    (10, None, None, -5),
    (10, None, None, -4),
    (10, None, None, -3),
    (10, None, None, -2),
    (10, None, None, -2),
    (10, None, None, -1),
    (10, None, None, 1),
    (10, None, None, 2),
    (10, None, None, 3),
    (10, None, None, 4),
    (10, None, None, 5),
    (10, None, None, 6),
    (10, None, None, 7),
    (10, None, None, 8),
    (10, None, None, 9),
    (10, None, None, 10),
    (10, None, None, 11),
    (10, None, None, 100),
    (10, -5, -1, None),
    (10, -5, 9, None),
    (10, 0, 10, 1),
    (10, 5, -1, None),
    (10, 5, 9, None),
    (10, 8, 4, -3),
    (10, 9, 0, -1),
    (10, 9, 8, -1),
    (10, 10, 0, -1),
    (100, None, -10, None),
    (100, None, 10, None),
    (100, None, 1000, None),
    (100, -10, None, None),
    (100, 10, None, None),
]


SLICE_EXAMPLES_GETITEM_RAISES = [
    (0, 8, 4, -3, 0),
    (10, None, None, -10, 1),
    (10, None, None, -5, 6),
    (10, None, None, -4, 9),
    (10, None, None, -3, 10),
    (10, None, None, -2, -6),
    (10, None, None, -2, 5),
    (10, None, None, -1, 10),
    (10, None, None, 1, 10),
    (10, None, None, 2, -6),
    (10, None, None, 2, 5),
    (10, None, None, 3, 10),
    (10, None, None, 4, 9),
    (10, None, None, 5, 6),
    (10, None, None, 10, 1),
    (10, -1, -5, None, 0),
    (10, -1, 5, None, 0),
    (10, 9, -5, None, 0),
    (10, 9, 0, -1, 9),
    (10, 9, 5, None, 0),
    (100, None, -1000, None, 0),
    (100, None, 0, None, 0),
    (100, None, 9, None, -10),
    (100, None, 10, None, 20),
    (100, 1000, None, None, -1),
    (100, 1000, None, None, 0),
]


SLICE_EXAMPLES_GETSLICE = [
    (10, None, None, None, slice(None, None, None)),
    (10, None, 0, None, slice(None, None, None)),
    (10, None, None, -100, slice(None, 2, None)),
    (10, None, None, -2, slice(None, 2, None)),
    (10, None, None, -2, slice(-2, None, None)),
    (10, None, None, -1, slice(None, None, -1)),
    (10, None, None, 2, slice(None, 2, None)),
    (10, None, None, 2, slice(-2, None, None)),
    (10, None, None, 100, slice(None, 2, None)),
    (10, None, 9, None, slice(None, None, -1)),
    (10, None, 9, None, slice(None, 2, -1)),
    (10, -5, -1, None, slice(None, 2, None)),
    (10, -5, -1, None, slice(-2, None, None)),
    (10, -5, 9, None, slice(None, 2, None)),
    (10, -5, 9, None, slice(-2, None, None)),
    (10, -1, -5, None, slice(None, 2, None)),
    (10, -1, 5, None, slice(None, 2, None)),
    (10, 0, None, -1, slice(None, None, -1)),
    (10, 3, None, -1, slice(4, None, -1)),
    (10, 3, None, -1, slice(4, 0, -1)),
    (10, 3, 0, -1, slice(4, None, -1)),
    (10, 3, 6, 1, slice(4, None, -1)),
    (10, 5, -1, None, slice(None, 2, None)),
    (10, 5, -1, None, slice(-2, None, None)),
    (10, 5, 9, None, slice(None, 2, None)),
    (10, 5, 9, None, slice(-2, None, None)),
    (10, 9, -5, None, slice(None, 2, None)),
    (10, 9, 0, -1, slice(None, 2, None)),
    (10, 9, 0, -1, slice(-2, None, None)),
    (10, 9, 5, None, slice(None, 2, None)),
    (100, None, -1000, None, slice(None, 2, None)),
    (100, None, -10, None, slice(None, 2, None)),
    (100, None, -10, None, slice(-2, None, None)),
    (100, None, -1, None, slice(-2, None, None)),
    (100, None, 10, None, slice(None, 2, None)),
    (100, None, 10, None, slice(-2, None, None)),
    (100, None, 1000, None, slice(None, 2, None)),
    (100, -1000, None, None, slice(None, 2, None)),
    (100, -10, None, None, slice(None, 2, None)),
    (100, -10, None, None, slice(-2, None, None)),
    (100, 10, None, None, slice(None, 2, None)),
    (100, 10, None, None, slice(-2, None, None)),
    (100, 1000, None, None, slice(None, 2, None)),
]


def createslices(
    size: int,
    start: Optional[int],
    stop: Optional[int],
    step: Optional[int],
) -> Tuple[lazysequence[int], List[int]]:
    """Create lazysequence and list slices for comparison."""
    iterable = range(size)
    indices = slice(start, stop, step)
    return (
        lazysequence(iterable)[indices],
        list(iterable)[indices],
    )


@pytest.mark.parametrize(SLICE_EXAMPLE_PARAMS, SLICE_EXAMPLES)
def test_slice_iter(
    size: int,
    start: Optional[int],
    stop: Optional[int],
    step: Optional[int],
) -> None:
    """It yields the same items as a list."""
    lazy, strict = createslices(size, start, stop, step)
    assert strict == list(iter(lazy))  # using `iter` explicitly avoids `len(s)`


@pytest.mark.parametrize(SLICE_EXAMPLE_PARAMS, SLICE_EXAMPLES)
def test_slice_bool(
    size: int,
    start: Optional[int],
    stop: Optional[int],
    step: Optional[int],
) -> None:
    """It returns the same boolean as a list."""
    lazy, strict = createslices(size, start, stop, step)
    assert bool(strict) is bool(lazy)


@pytest.mark.parametrize(SLICE_EXAMPLE_PARAMS, SLICE_EXAMPLES)
def test_slice_release(
    size: int,
    start: Optional[int],
    stop: Optional[int],
    step: Optional[int],
) -> None:
    """It yields the same items as a list."""
    lazy, strict = createslices(size, start, stop, step)
    assert strict == list(lazy.release())


@pytest.mark.parametrize(SLICE_EXAMPLE_PARAMS, SLICE_EXAMPLES)
def test_slice_len(
    size: int,
    start: Optional[int],
    stop: Optional[int],
    step: Optional[int],
) -> None:
    """It has the same length as a list."""
    lazy, strict = createslices(size, start, stop, step)
    assert len(strict) == len(lazy)


@pytest.mark.parametrize(SLICE_EXAMPLE_PARAMS, SLICE_EXAMPLES_GETITEM)
@pytest.mark.parametrize("index", [0, -1])
def test_slice_getitem(
    size: int,
    start: Optional[int],
    stop: Optional[int],
    step: Optional[int],
    index: int,
) -> None:
    """It returns the same item as a list."""
    lazy, strict = createslices(size, start, stop, step)
    assert strict[index] == lazy[index]


@pytest.mark.parametrize(
    SLICE_EXAMPLE_PARAMS + ("index",),
    SLICE_EXAMPLES_GETITEM_RAISES,
)
def test_slice_getitem_raises(
    size: int,
    start: Optional[int],
    stop: Optional[int],
    step: Optional[int],
    index: int,
) -> None:
    """It raises an exception."""
    s = lazysequence(range(size))
    s = s[start:stop:step]
    with pytest.raises(IndexError):
        s[index]


@pytest.mark.parametrize(
    SLICE_EXAMPLE_PARAMS + ("indices",),
    SLICE_EXAMPLES_GETSLICE,
    ids=str,
)
def test_slice_of_slice(
    size: int,
    start: Optional[int],
    stop: Optional[int],
    step: Optional[int],
    indices: slice,
) -> None:
    """It contains the same items as a list."""
    lazy, strict = createslices(size, start, stop, step)
    assert strict[indices] == list(lazy[indices])


def test_interleaved_iteration() -> None:
    """It allows simultaneous iteration over multiple related instances."""
    lazy, strict = lazysequence(range(5)), list(range(5))

    def transform(s: Sequence[int]) -> List[Tuple[int, int]]:
        return list(zip(s, s[1:]))

    assert transform(strict) == transform(lazy)


def test_cache_mutation_during_iteration() -> None:
    """It allows the cache to be mutated during iteration."""
    s = lazysequence(range(5))
    a, b = iter(s), iter(s)
    next(a)
    next(b)
    next(a)
    next(b)
