#!/usr/bin/env python3-allemande

"""
Benchmark different methods of finding the second largest number in a list.
"""

import time
import random
import heapq
import logging
from typing import Callable

from ally import main, logs, geput  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def via_sort(numbers: list[int]) -> int:
    """Find second largest by sorting."""
    return sorted(numbers)[-2]


def via_heapq(numbers: list[int]) -> int:
    """Find second largest using heapq.nlargest."""
    return heapq.nlargest(2, numbers)[1]


def via_variables(numbers: list[int]) -> int:
    """Find second largest by tracking two variables in one pass."""
    largest = max(numbers[0], numbers[1])
    second = min(numbers[0], numbers[1])

    for num in numbers[2:]:
        if num > largest:
            second = largest
            largest = num
        elif num > second and num != largest:
            second = num
    return second


def via_remove_max(numbers: list[int]) -> int:
    """Find second largest by removing one instance of max."""
    nums = numbers.copy()
    first_max = max(nums)
    nums.remove(first_max)
    return max(nums)


def benchmark(size: int, numbers: list[int], print) -> None:
    """Run benchmarks for all methods on a list of given size."""
    methods: dict[str, Callable[[list[int]], int]] = {
        "Sort": via_sort,
        "Heapq": via_heapq,
        "Variables": via_variables,
        "Remove Max": via_remove_max,
    }

    print(f"\nBenchmarking list size: {size}")
    print("-" * 40)

    for name, method in methods.items():
        start = time.perf_counter()
        result = method(numbers)
        elapsed = time.perf_counter() - start
        print(f"{name:12} Time: {elapsed:.6f}s Result: {result}")


def second_largest(get, put, sizes: list[int] | None = None) -> None:
    """Benchmark different methods of finding the second largest number."""
    print = geput.print(put)

    if sizes is None:
        sizes = [10, 100, 1000, 1_000_000]

    for size in sizes:
        numbers = random.choices(range(size * 10), k=size)
        benchmark(size, numbers, print)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-s", "--sizes", nargs="+", type=int, help="list sizes to benchmark")


if __name__ == "__main__":
    main.go(second_largest, setup_args)
