import pytest
from subtract_time import subtract_times, InvalidTimeFormatError

def test_subtract_times():
    assert subtract_times("12:34", "11:22") == "01:12"
    assert subtract_times("24:00", "23:59") == "00:01"
    assert subtract_times("23:59", "00:00") == "23:59"
    assert subtract_times("12:34", "12:34") == "00:00"
    assert subtract_times("20:45", "22:30") == "-01:45"

def test_negative_result():
    assert subtract_times("10:10", "20:20") == "-10:10"

def test_garbage_input():
    with pytest.raises(InvalidTimeFormatError):
        subtract_times("12:60", "11:XX")
