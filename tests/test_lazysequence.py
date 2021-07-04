"""Unit tests for lazysequence."""
from typing import Any

import pytest
from _pytest.mark import ParameterSet

from lazysequence import lazysequence


def xfail(*args: Any) -> ParameterSet:
    """Mark parameters as XFAIL."""
    return pytest.param(*args, marks=pytest.mark.xfail)


def test_init() -> None:
    """It is created from an iterable."""
    lazysequence([])


def test_init_storage() -> None:
    """It uses the factory to create its cache."""
    s = lazysequence([1, 2, 3], storage=list)
    a, b, c = s
    assert (1, 2, 3) == (a, b, c)


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
    # It's best to avoid this technique. Slicing returns a new lazy sequence on
    # top of the old one. This is inherently recursive, and repeated slicing of
    # large sequences can result in a RecursionError. Try `s = s[10:]` to see
    # this happen. You can improve the situation by using `s.release()` followed
    # by `itertools.islice`, and construct the new lazy sequence from that.

    s = lazysequence(range(10000))
    while s:
        s = s[100:]
    assert not s


def test_init_step_raises() -> None:
    """."""
    with pytest.raises(ValueError, match="slice step cannot be zero"):
        lazysequence(range(10), step=0)


@pytest.mark.parametrize(
    ("size", "start", "expected"),
    [
        (100, 10, 10),
        (100, -10, 90),
        (100, -1000, 0),
    ],
)
def test_iter_start(size: int, start: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    item = next(iter(s))
    assert expected == item


@pytest.mark.parametrize(
    ("size", "stop", "bound"),
    [
        (100, 10, 10),
        (100, -10, 90),
        (100, -1000, 0),
    ],
)
def test_iter_stop(size: int, stop: int, bound: int) -> None:
    """."""
    s = lazysequence(range(size), stop=stop)
    assert all(item < bound for item in s)


@pytest.mark.parametrize(
    ("size", "start", "stop", "expected"),
    [
        (10, 5, 9, [5, 6, 7, 8]),
        (10, 5, -1, [5, 6, 7, 8]),
        (10, -5, 9, [5, 6, 7, 8]),
        (10, -5, -1, [5, 6, 7, 8]),
        (10, 9, 5, []),
        (10, 9, -5, []),
        (10, -1, 5, []),
        (10, -1, -5, []),
    ],
)
def test_iter_start_and_stop(
    size: int, start: int, stop: int, expected: list[int]
) -> None:
    """."""
    s = lazysequence(range(size), start=start, stop=stop)
    assert expected == list(s)


@pytest.mark.parametrize(
    ("size", "step", "expected"),
    [
        (10, 1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        (10, 2, [0, 2, 4, 6, 8]),
    ],
)
def test_iter_step(size: int, step: int, expected: list[int]) -> None:
    """."""
    s = lazysequence(range(size), step=step)
    assert expected == list(s)


@pytest.mark.parametrize(
    ("size", "start"),
    [
        (100, 1000),
    ],
)
def test_iter_raises_start(size: int, start: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    with pytest.raises(StopIteration):
        next(iter(s))


@pytest.mark.parametrize(
    ("size", "start", "expected"),
    [
        (100, 100, False),
        (0, -1, False),
        (1, -1, True),
    ],
)
def test_bool_start(size: int, start: int, expected: bool) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    assert bool(s) is expected


@pytest.mark.parametrize(
    ("size", "stop", "expected"),
    [
        (0, 0, False),
        (0, 1, False),
        (1, 0, False),
        (1, 1, True),
        (2, 1, True),
        (0, -1, False),
        (1, -1, False),
        (2, -1, True),
        (2, -2, False),
        (2, -3, False),
    ],
)
def test_bool_stop(size: int, stop: int, expected: bool) -> None:
    """."""
    s = lazysequence(range(size), stop=stop)
    assert bool(s) == expected


@pytest.mark.parametrize(
    ("size", "start", "expected"),
    [
        (100, 10, 10),
        (100, -10, 90),
    ],
)
def test_release_start(size: int, start: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    item = next(s.release())
    assert expected == item


@pytest.mark.parametrize(
    ("size", "stop", "bound"),
    [
        (100, 10, 10),
        (100, -10, 90),
        (100, -1000, 0),
    ],
)
def test_release_stop(size: int, stop: int, bound: int) -> None:
    """."""
    s = lazysequence(range(size), stop=stop)
    assert all(item < bound for item in s.release())


@pytest.mark.parametrize(
    ("size", "step", "expected"),
    [
        (10, 1, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
        (10, 2, [0, 2, 4, 6, 8]),
    ],
)
def test_release_step(size: int, step: int, expected: list[int]) -> None:
    """."""
    s = lazysequence(range(size), step=step)
    assert expected == list(s.release())


@pytest.mark.parametrize(
    ("size", "start", "expected"),
    [
        (100, 10, 90),
        (100, 1000, 0),
        (100, -10, 10),
    ],
)
def test_len_start(size: int, start: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    assert expected == len(s)


@pytest.mark.parametrize(
    ("size", "stop", "expected"),
    [
        (100, 10, 10),
        (100, 1000, 100),
        (100, -10, 90),
    ],
)
def test_len_stop(size: int, stop: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), stop=stop)
    assert expected == len(s)


@pytest.mark.parametrize(
    ("size", "start", "stop", "expected"),
    [
        (10, 5, 9, 4),
        (10, 5, -1, 4),
        (10, -5, 9, 4),
        (10, -5, -1, 4),
        (10, 9, 5, 0),
        (10, 9, -5, 0),
        (10, -1, 5, 0),
        (10, -1, -5, 0),
    ],
)
def test_len_start_and_stop(size: int, start: int, stop: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), start=start, stop=stop)
    assert expected == len(s)


@pytest.mark.parametrize(
    ("size", "step", "expected"),
    [
        (10, 1, 10),
        (10, 2, len([0, 2, 4, 6, 8])),
        (10, 3, len([0, 3, 6, 9])),
        (10, 4, len([0, 4, 8])),
        (10, 5, len([0, 5])),
        (10, 6, len([0, 6])),
        (10, 7, len([0, 7])),
        (10, 8, len([0, 8])),
        (10, 9, len([0, 9])),
        (10, 10, len([0])),
        (10, 11, len([0])),
        (10, 100, len([0])),
    ],
)
def test_len_step(size: int, step: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), step=step)
    assert expected == len(s)


@pytest.mark.parametrize(
    ("size", "start", "index", "expected"),
    [
        (100, 10, 0, 10),
        (100, 10, -1, 99),
        (100, -10, 0, 90),
        (100, -10, -1, 99),
    ],
)
def test_getitem_start(size: int, start: int, index: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    assert expected == s[index]


@pytest.mark.parametrize(
    ("size", "stop", "index", "expected"),
    [
        (100, 10, 0, 0),
        (100, 10, -1, 9),
        (100, 1000, 0, 0),
        (100, 1000, -1, 99),
        (100, -10, 0, 0),
        (100, -10, -1, 89),
    ],
)
def test_getitem_stop(size: int, stop: int, index: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), stop=stop)
    assert expected == s[index]


@pytest.mark.parametrize(
    ("size", "step", "index", "expected"),
    [
        (10, 1, 0, 0),
        (10, 2, 0, 0),
        (10, 1, -1, 9),
        (10, 2, -1, 8),
        (10, 3, -1, 9),
        (10, 4, -1, 8),
        (10, 5, -1, 5),
        (10, 6, -1, 6),
        (10, 7, -1, 7),
        (10, 8, -1, 8),
        (10, 9, -1, 9),
        (10, 10, -1, 0),
        (10, 11, -1, 0),
        (10, 100, -1, 0),
    ],
)
def test_getitem_step(size: int, step: int, index: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), step=step)
    assert expected == s[index]


@pytest.mark.parametrize(
    ("size", "start", "stop", "index", "expected"),
    [
        (10, 5, 9, 0, 5),
        (10, 5, 9, -1, 8),
        (10, 5, -1, 0, 5),
        (10, 5, -1, -1, 8),
        (10, -5, 9, 0, 5),
        (10, -5, 9, -1, 8),
        (10, -5, -1, 0, 5),
        (10, -5, -1, -1, 8),
    ],
)
def test_getitem_start_and_stop(
    size: int, start: int, stop: int, index: int, expected: int
) -> None:
    """."""
    s = lazysequence(range(size), start=start, stop=stop)
    assert expected == s[index]


@pytest.mark.parametrize(
    ("size", "start", "index"),
    [
        (100, 1000, 0),
        (100, 1000, -1),
    ],
)
def test_getitem_raises_start(size: int, start: int, index: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    with pytest.raises(IndexError):
        s[index]


@pytest.mark.parametrize(
    ("size", "stop", "index"),
    [
        (100, 0, 0),
        (100, 10, 20),
        (100, 9, -10),
        (100, -1000, 0),
    ],
)
def test_getitem_raises_stop(size: int, stop: int, index: int) -> None:
    """It raises IndexError."""
    s = lazysequence(range(size), stop=stop)
    with pytest.raises(IndexError):
        s[index]


@pytest.mark.parametrize(
    ("size", "start", "stop", "index"),
    [
        (10, 9, 5, 0),
        (10, 9, -5, 0),
        (10, -1, 5, 0),
        (10, -1, -5, 0),
    ],
)
def test_getitem_raises_start_and_stop(
    size: int, start: int, stop: int, index: int
) -> None:
    """."""
    s = lazysequence(range(size), start=start, stop=stop)
    with pytest.raises(IndexError):
        s[index]


@pytest.mark.parametrize(
    ("size", "step", "index"),
    [
        (10, 1, 10),
        (10, 2, 5),
        (10, 3, 10),
        (10, 4, 9),
        (10, 5, 6),
        (10, 10, 1),
        (10, 2, -6),
    ],
)
def test_getitem_raises_step(size: int, step: int, index: int) -> None:
    """It raises IndexError."""
    s = lazysequence(range(size), step=step)
    with pytest.raises(IndexError):
        s[index]


@pytest.mark.parametrize(
    ("size", "start", "indices", "expected"),
    [
        (100, 10, slice(2), (10, 11)),
        (100, 10, slice(-2, None), (98, 99)),
        (100, -10, slice(2), (90, 91)),
        (100, -10, slice(-2, None), (98, 99)),
        (100, 1000, slice(2), ()),
        (100, -1000, slice(2), (0, 1)),
    ],
)
def test_slice_start(
    size: int, start: int, indices: slice, expected: tuple[int, ...]
) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    result = tuple(s[indices])
    assert expected == result


@pytest.mark.parametrize(
    ("size", "stop", "indices", "expected"),
    [
        (100, 10, slice(2), (0, 1)),
        (100, 10, slice(-2, None), (8, 9)),
        (100, -10, slice(2), (0, 1)),
        (100, -10, slice(-2, None), (88, 89)),
        (100, 1000, slice(2), (0, 1)),
        (100, -1000, slice(2), ()),
        (100, -1, slice(-2, None), (97, 98)),
    ],
)
def test_slice_stop(
    size: int, stop: int, indices: slice, expected: tuple[int, ...]
) -> None:
    """."""
    s = lazysequence(range(size), stop=stop)
    result = tuple(s[indices])
    assert expected == result


@pytest.mark.parametrize(
    ("size", "start", "stop", "indices", "expected"),
    [
        (10, 5, 9, slice(2), [5, 6]),
        (10, 5, 9, slice(-2, None), [7, 8]),
        (10, 5, -1, slice(2), [5, 6]),
        (10, 5, -1, slice(-2, None), [7, 8]),
        (10, -5, 9, slice(2), [5, 6]),
        (10, -5, 9, slice(-2, None), [7, 8]),
        (10, -5, -1, slice(2), [5, 6]),
        (10, -5, -1, slice(-2, None), [7, 8]),
        (10, 9, 5, slice(2), []),
        (10, 9, -5, slice(2), []),
        (10, -1, 5, slice(2), []),
        (10, -1, -5, slice(2), []),
    ],
)
def test_slice_start_and_stop(
    size: int, start: int, stop: int, indices: slice, expected: list[int]
) -> None:
    """."""
    s = lazysequence(range(size), start=start, stop=stop)
    result = list(s[indices])
    assert expected == result


@pytest.mark.parametrize(
    ("size", "step", "indices", "expected"),
    [
        (10, 2, slice(2), [0, 2]),
        (10, 2, slice(-2, None), [6, 8]),
        (10, 100, slice(2), [0]),
    ],
)
def test_slice_step(size: int, step: int, indices: slice, expected: list[int]) -> None:
    """."""
    s = lazysequence(range(size), step=step)
    result = list(s[indices])
    assert expected == result
