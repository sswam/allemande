import pytest
from subtract_time import subtract_times, InvalidTimeFormatError

def test_subtract_times():
    assert subtract_times("12:34", "11:22") == "01:12"
    assert subtract_times("00:00", "23:59") == "00:01"
    assert subtract_times("23:59", "00:00") == "23:59"
    assert subtract_times("12:34", "12:34") == "00:00"
    assert subtract_times("20:45", "22:30") == "22:15"

def test_invalid_time_format():
    with pytest.raises(InvalidTimeFormatError):
        subtract_times("12:60", "11:22")
    with pytest.raises(InvalidTimeFormatError):
        subtract_times("abc:de", "11:22")
    with pytest.raises(InvalidTimeFormatError):
        subtract_times("12:34", "xy:zw")
    with pytest.raises(InvalidTimeFormatError):
        subtract_times("25:00", "11:22")
