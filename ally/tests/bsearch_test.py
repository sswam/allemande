import pytest
from typing import Any
import random

import ally.bsearch as subject  # type: ignore

subject_name = subject.__name__

def test_find_lowest_int_true_basic():
    # Test basic ascending sequence
    pred = lambda x: x >= 5
    assert subject.find_lowest_int_true(pred) == 5

    # Test with offset start
    assert subject.find_lowest_int_true(pred, start=3) == 5
    assert subject.find_lowest_int_true(pred, start=6) == 6

def test_find_lowest_int_true_immediate():
    # Test when predicate is immediately true
    pred = lambda x: x >= 0
    assert subject.find_lowest_int_true(pred) == 0

    # Test when predicate is true at start point
    assert subject.find_lowest_int_true(pred, start=10) == 10

def test_find_lowest_int_true_large_gap():
    # Test when true value is far from start
    pred = lambda x: x >= 1000
    assert subject.find_lowest_int_true(pred) == 1000

    # Test with negative start
    assert subject.find_lowest_int_true(pred, start=-500) == 1000

def test_find_lowest_int_true_complex():
    # Test with more complex predicate
    pred = lambda x: x * x >= 100
    assert subject.find_lowest_int_true(pred) == 10

def test_find_lowest_int_true_performance():
    # Test that we don't do linear search for large values
    pred = lambda x: x >= 1_000_000

    # Should complete quickly due to exponential search
    result = subject.find_lowest_int_true(pred)
    assert result == 1_000_000

@pytest.mark.parametrize("target,start", [
    (5, 0),
    (0, 0),
    (1000, -1000),
    (10, 5),
    (100, 99),
])
def test_find_lowest_int_true_parametrized(target, start):
    pred = lambda x: x >= target
    assert subject.find_lowest_int_true(pred, start=start) == target

def test_find_lowest_int_true_function_calls():
    # Test that we're not making too many predicate calls
    call_count = 0
    def counting_pred(x):
        nonlocal call_count
        call_count += 1
        return x >= 100

    result = subject.find_lowest_int_true(counting_pred)
    assert result == 100
    # For finding 100, we shouldn't need more than ~15 calls
    # (about 7 for exponential search and 7 for binary search)
    assert call_count < 15

def test_find_lowest_int_true_edge_cases():
    # Test consecutive predicate transitions
    pred = lambda x: x >= 1
    assert subject.find_lowest_int_true(pred) == 1

    # Test predicate that becomes true after several steps
    steps = []
    def stepping_pred(x):
        steps.append(x)
        return x >= 3

    result = subject.find_lowest_int_true(stepping_pred)
    assert result == 3
    # Check that we tried the right values
    assert steps == [0, 1, 3, 2]

def test_with_random_targets():
    for _ in range(100):
        target = random.randint(0, 1023)
        start = 0
        steps = []
        def stepping_pred(x):
            steps.append(x)
            return x >= target
        assert subject.find_lowest_int_true(stepping_pred, start=start) == target
        # check steps are unique
        assert len(steps) == len(set(steps))
        # check not too many steps
        assert len(steps) <= 20
