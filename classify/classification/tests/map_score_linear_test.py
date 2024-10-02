import pytest
from map_score_linear import map_score

@pytest.mark.parametrize("old_score, expected_new_score", [
	(0.0, 0.0),
	(0.5, 0.5),
	(1.0, 1.0),
	(1.5, 2.0),
	(2.0, 3.0),
	(2.5, 4.0),
	(3.0, 5.0),
	(3.5, 6.0),
	(4.0, 7.0),
	(4.5, 8.0),
	(5.0, 9.0),
	(5.5, 9.5),
	(6.0, 10.0),
])
def test_map_score_valid_inputs(old_score, expected_new_score):
	assert map_score(old_score) == pytest.approx(expected_new_score)

def test_map_score_none_input():
	assert map_score(None) == 10.0

@pytest.mark.parametrize("invalid_score, expected_new_score", [
	(-1.0, 0.0),
	(7.0, 10.0),
	(100.0, 10.0),
])
def test_map_score_invalid_inputs(invalid_score, expected_new_score):
	assert map_score(invalid_score) == pytest.approx(expected_new_score)

@pytest.mark.parametrize("old_score", [0.1, 0.9, 1.1, 1.9, 2.1, 2.9, 3.1, 3.9, 4.1, 4.9, 5.1, 5.9])
def test_map_score_intermediate_values(old_score):
	new_score = map_score(old_score)
	assert 0.0 <= new_score <= 10.0

	# Check if the new score is within the expected range
	if 0.0 <= old_score <= 1.0:
		assert 0.0 <= new_score <= 1.0
	elif 1.0 < old_score <= 2.0:
		assert 1.0 < new_score <= 3.0
	elif 2.0 < old_score <= 3.0:
		assert 3.0 < new_score <= 5.0
	elif 3.0 < old_score <= 4.0:
		assert 5.0 < new_score <= 7.0
	elif 4.0 < old_score <= 5.0:
		assert 7.0 < new_score <= 9.0
	else:  # 5.0 < old_score <= 6.0
		assert 9.0 < new_score <= 10.0

def test_map_score_float_precision():
	assert map_score(1.75) == pytest.approx(2.5)
	assert map_score(3.25) == pytest.approx(5.5)
	assert map_score(5.75) == pytest.approx(9.75)

if __name__ == "__main__":
	pytest.main([__file__])
