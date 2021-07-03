"""Unit tests for lazysequence."""
import pytest

from lazysequence import lazysequence


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


@pytest.mark.parametrize(
    ("size", "start", "expected"),
    [
        (100, 10, 10),
        (100, -10, 90),
        (100, -1000, 0),
    ],
)
def test_start_iter(size: int, start: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    item = next(iter(s))
    assert expected == item


@pytest.mark.parametrize(
    ("size", "start"),
    [
        (100, 1000),
    ],
)
def test_start_iter_raises(size: int, start: int) -> None:
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
def test_start_bool(size: int, start: int, expected: bool) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    assert bool(s) is expected


@pytest.mark.parametrize(
    ("size", "start", "expected"),
    [
        (100, 10, 10),
        (100, -10, 90),
    ],
)
def test_start_release(size: int, start: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    item = next(s.release())
    assert expected == item


@pytest.mark.parametrize(
    ("size", "start", "expected"),
    [
        (100, 10, 90),
        (100, 1000, 0),
        (100, -10, 10),
    ],
)
def test_start_len(size: int, start: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
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
def test_start_getitem(size: int, start: int, index: int, expected: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    assert expected == s[index]


@pytest.mark.parametrize(
    ("size", "start", "index"),
    [
        (100, 1000, 0),
        (100, 1000, -1),
    ],
)
def test_start_getitem_raises(size: int, start: int, index: int) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    with pytest.raises(IndexError):
        s[index]


@pytest.mark.parametrize(
    ("size", "start", "indices", "expected"),
    [
        (100, 10, slice(2), (10, 11)),
        (100, 10, slice(-2, None), (98, 99)),
        (100, -10, slice(2), (90, 91)),
        (100, -10, slice(-2, None), (98, 99)),
    ],
)
def test_start_slice(
    size: int, start: int, indices: slice, expected: tuple[int, ...]
) -> None:
    """."""
    s = lazysequence(range(size), start=start)
    a, b = s[indices]
    assert expected == (a, b)


@pytest.mark.parametrize(
    ("size", "stop"),
    [
        (100, 10),
    ],
)
def test_stop_iter(size: int, stop: int) -> None:
    """."""
    s = lazysequence(range(size), stop=stop)
    assert all(item < stop for item in s)


@pytest.mark.parametrize(
    ("size", "stop", "expected"),
    [
        (1, 0, False),
        (2, 1, True),
    ],
)
def test_stop_bool_empty(size: int, stop: int, expected: bool) -> None:
    """."""
    s = lazysequence(range(size), stop=stop)
    assert bool(s) == expected


@pytest.mark.parametrize(
    ("size", "stop"),
    [
        (100, 10),
    ],
)
def test_stop_release(size: int, stop: int) -> None:
    """."""
    s = lazysequence(range(size), stop=stop)
    assert all(item < stop for item in s.release())
