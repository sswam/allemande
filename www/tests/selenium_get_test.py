import json
import tempfile
import unittest.mock
from pathlib import Path, PosixPath

from selenium_get import load_cookies, save_cookies, set_cookies, scroll_page, run_script, selenium_get_2


def test_load_cookies_none():
    result = load_cookies(None)
    assert result == []


def test_load_cookies_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        cookie_file = Path(tmpdir) / "cookies.json"
        cookies = [{"name": "test", "value": "value"}]
        cookie_file.write_text(json.dumps(cookies))
        result = load_cookies(cookie_file)
        assert result == cookies


def test_save_cookies_none():
    save_cookies(None, [])
    # No assertion, just no error


def test_save_cookies_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        cookie_file = Path(tmpdir) / "cookies.json"
        cookies = [{"name": "test", "value": "value"}]
        save_cookies(cookie_file, cookies)
        with cookie_file.open("r") as f:
            saved = json.load(f)
        assert saved == cookies


def test_set_cookies():
    wd = unittest.mock.Mock()
    cookies = [{"name": "test"}]
    set_cookies(wd, cookies)
    wd.execute_cdp_cmd.assert_any_call("Network.enable", {})
    wd.execute_cdp_cmd.assert_any_call("Network.setCookie", {"name": "test"})
    wd.execute_cdp_cmd.assert_any_call("Network.disable", {})


def test_run_script_no_exe():
    wd = unittest.mock.Mock()
    run_script(wd, "")
    wd.execute_script.assert_not_called()


def test_run_script_success():
    wd = unittest.mock.Mock()
    wd.execute_script.return_value = None
    run_script(wd, "alert('test')")
    wd.execute_script.assert_called_once_with("alert('test')")


def test_run_script_retry():
    wd = unittest.mock.Mock()
    wd.execute_script.side_effect = [Exception("Error 1"), Exception("Error 2"), None]
    run_script(wd, "alert('test')", retry_script=3)
    assert wd.execute_script.call_count == 3


def test_scroll_page_no_selector():
    wd = unittest.mock.Mock()
    wd.execute_script.side_effect = [1000, 0, 900, 900]  # max_scroll, scrolled, after scroll, same
    scroll_page(wd, selector=None, time_limit=1)
    # Check calls
    calls = wd.execute_script.call_args_list
    assert len(calls) >= 2 # At least 2 calls for initial height and scroll, then potentially more
    assert calls[0].args[0] == "return document.body.scrollHeight"
    assert calls[1].args[0] == "window.scrollTo(0, document.body.scrollHeight);"
    # Simulate a scenario where scrolling stops because no more scroll height is added
    wd = unittest.mock.Mock()
    # First, get total height (1000)
    # Then, scroll (scrolled amount 0, current pos 0) -> scroll to 1000
    # Then, get total height again (1000, no change)
    wd.execute_script.side_effect = [
        1000,  # initial scrollHeight
        0,     # window.pageYOffset (after initial scroll)
        1000,  # scrollHeight after first scroll attempt
    ]
    scroll_page(wd, selector=None, time_limit=1)
    assert wd.execute_script.call_count == 3
    # The first call is for document.body.scrollHeight
    assert "document.body.scrollHeight" in wd.execute_script.call_args_list[0].args[0]
    # The second call is for window.scrollTo
    assert "window.scrollTo" in wd.execute_script.call_args_list[1].args[0]


# Additional tests can be added for scroll_page with selector, selenium_get_2, but they require more mocking

# Ideas: Mock webdriver for selenium_get_2 to test logic without actual browser. Use fixtures for common mocks. Test edge cases like empty cookies, invalid cookie file.
