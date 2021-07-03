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


def test_start_getitem() -> None:
    """."""
    s = lazysequence(range(100), start=10)
    assert 10 == s[0]


def test_start_getitem_negative() -> None:
    """."""
    s = lazysequence(range(100), start=10)
    assert 99 == s[-1]


def test_start_iter() -> None:
    """."""
    s = lazysequence(range(100), start=10)
    item = next(iter(s))
    assert 10 == item


def test_start_bool() -> None:
    """."""
    s = lazysequence(range(100), start=100)
    assert not s


def test_start_release() -> None:
    """."""
    s = lazysequence(range(100), start=10)
    item = next(s.release())
    assert 10 == item


def test_start_len() -> None:
    """."""
    s = lazysequence(range(100), start=10)
    assert 90 == len(s)


def test_start_slice() -> None:
    """."""
    s = lazysequence(range(100), start=10)
    a, b = s[:2]
    assert (10, 11) == (a, b)


def test_start_slice_negative() -> None:
    """."""
    s = lazysequence(range(100), start=10)
    a, b = s[-2:]
    assert (98, 99) == (a, b)


def test_negative_start_iter() -> None:
    """."""
    s = lazysequence(range(100), start=-10)
    item = next(iter(s))
    assert 90 == item


def test_negative_start_getitem() -> None:
    """."""
    s = lazysequence(range(100), start=-10)
    assert 90 == s[0]


def test_negative_start_getitem_negative() -> None:
    """."""
    s = lazysequence(range(100), start=-10)
    assert 99 == s[-1]


def test_negative_start_bool_empty() -> None:
    """."""
    s: lazysequence[int] = lazysequence([], start=-1)
    assert not s


def test_negative_start_bool_nonempty() -> None:
    """."""
    s = lazysequence([0], start=-1)
    assert s


def test_negative_start_release() -> None:
    """."""
    s = lazysequence(range(100), start=-10)
    item = next(s.release())
    assert 90 == item


def test_negative_start_len() -> None:
    """."""
    s = lazysequence(range(100), start=-10)
    assert 10 == len(s)


def test_negative_start_slice() -> None:
    """."""
    s = lazysequence(range(100), start=-10)
    a, b = s[:2]
    assert (90, 91) == (a, b)


def test_negative_start_slice_negative() -> None:
    """."""
    s = lazysequence(range(100), start=-10)
    a, b = s[-2:]
    assert (98, 99) == (a, b)


def test_stop_iter() -> None:
    """."""
    s = lazysequence(range(100), stop=10)
    assert all(item < 10 for item in s)


def test_stop_bool_empty() -> None:
    """."""
    s: lazysequence[int] = lazysequence([0], stop=0)
    assert not s


def test_stop_bool_nonempty() -> None:
    """."""
    s = lazysequence([0, 1], stop=1)
    assert s


def test_stop_release() -> None:
    """."""
    s = lazysequence(range(100), stop=10)
    assert all(item < 10 for item in s.release())
