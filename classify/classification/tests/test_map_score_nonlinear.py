# Version 1.1.5

import pytest
from map_score_nonlinear import map_score, calculate_parameters

# Test cases for map_score function
@pytest.mark.parametrize("old_score, expected", [
	(0.0, 0.0),
	(1.0, 1.0),
	(3.0, 5.0),
	(5.0, 9.0),
	(6.0, 10.0),
	(-1.0, 0.0),  # Test lower bound
	(7.0, 10.0),  # Test upper bound
])
def test_map_score(old_score, expected):
	a, b, c = calculate_parameters((0.0, 0.0), (6.0, 10.0))
	assert map_score(old_score, a, b, c) == pytest.approx(expected, abs=0.02)
