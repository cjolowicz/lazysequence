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


def test_outofrange() -> None:
    """It raises IndexError."""
    s: lazysequence[int] = lazysequence([])
    with pytest.raises(IndexError):
        s[0]


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
