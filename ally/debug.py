import cProfile
import pstats
from pstats import SortKey
import logging

logger = logging.getLogger(__name__)

def profile_function(func, *args, **kwargs) -> object:
    """Profile the execution of a function call and display performance statistics.

    Returns the result of the profiled function call.
    """
    profiler = cProfile.Profile()
    loc = locals()
    profiler.runctx("result = func(*args, **kwargs)", globals(), loc)
    result = loc['result']

    # Create stats object and print top rows sorted by cumulative time
    stats = pstats.Stats(profiler).sort_stats(SortKey.CUMULATIVE)

    stats.print_stats()

    return result
