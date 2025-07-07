An API summary and cheatsheet for Playwright (Python).

### Test Structure & Execution

Tests are Python functions that accept `pytest` fixtures, like `page`.

```python
# test_example.py
from playwright.sync_api import Page, expect

def test_example(page: Page):
    page.goto("https://playwright.dev/")
    expect(page).to_have_title("Playwright")
```

- **Fixtures (Hooks)**: Use `@pytest.fixture` for setup/teardown.
  - `scope="function"` (default): Runs for each test (e.g., `beforeEach`/`afterEach`).
  - `scope="module"`: Runs once per test file (e.g., `beforeAll`/`afterAll`).
- **Page Object Model (POM)**: A pattern to create reusable, high-level APIs for your pages.
  ```python
  class MyPage:
      def __init__(self, page: Page):
          self.page = page
          self.my_button = page.get_by_role("button", name="My Button")

      def do_something(self, data):
          self.my_button.click()
          # ...
  ```

### Debugging

- **Inspector**: `PWDEBUG=1 pytest`. A GUI for stepping through tests.
- **`page.pause()`**: Pauses test execution and opens the Inspector.
- **Console Debugging**: `PWDEBUG=console pytest`. Exposes a `playwright` object in the browser's DevTools console for live queries.
  - `playwright.$('selector')`: Query for a single element.
  - `playwright.$$('selector')`: Query for all matching elements.
  - `playwright.inspect('selector')`: Reveal element in the Elements panel.
  - `playwright.locator(...)`: Create a locator.
- **Verbose Logs**: `DEBUG=pw:api pytest`

---

## Locators

Locators are the central piece of Playwright, representing how to find an element. They are auto-waiting and resilient to page changes.

### Creating Locators

These are the recommended, user-facing locators.

| Method | Description |
| --- | --- |
| `page.get_by_role(role, **kwargs)` | Locate by ARIA role, name, etc. (e.g., `role="button"`, `name="Submit"`) |
| `page.get_by_text(text, exact=False)` | Locate by text content (string or regex). |
| `page.get_by_label(text, exact=False)` | Locate a form control by its associated `<label>`. |
| `page.get_by_placeholder(text, exact=False)` | Locate an input by its placeholder. |
| `page.get_by_alt_text(text, exact=False)` | Locate an element by its `alt` text (e.g., `<img>`). |
| `page.get_by_title(text, exact=False)` | Locate an element by its `title` attribute. |
| `page.get_by_test_id(test_id)` | Locate by `data-testid` attribute (configurable). |
| `page.locator(selector)` | Fallback for CSS or XPath selectors. Less resilient. |
| `page.frame_locator(selector)` | Locate an `<iframe>` to then find elements within it. |

### Filtering & Chaining Locators

- **Chaining**: `page.get_by_role("list").get_by_role("listitem")`
- **Filtering**:
  - `locator.filter(has_text=str|re, has_not_text=str|re, has=Locator, has_not=Locator)`: Narrows down a set of locators.
- **Combining**:
  - `locator.or_(other)`: Matches elements from either locator.
  - `locator.and_(other)`: Narrows a locator to also match another.

### Handling Lists of Elements

- `locator.first`: Locator for the first matching element.
- `locator.last`: Locator for the last matching element.
- `locator.nth(index)`: Locator for the element at a specific index (0-based).
- `locator.count()`: Returns the number of matching elements.
- `locator.all()`: Returns a `List[Locator]` for iteration.

---

## Actions

Actions are performed on `Locator` objects. For async tests, prefix calls with `await`. Playwright auto-waits for elements to be actionable before performing actions.

| Action | Description |
| --- | --- |
| `page.goto(url)` | Navigates the page to a URL. |
| `locator.click(**kwargs)` | Clicks an element. Args: `button`, `modifiers`, `position`, `force=True` (to bypass actionability checks). |
| `locator.dblclick()` | Double-clicks an element. |
| `locator.fill(value)` | Clears and fills a text input. |
| `locator.press(key)` | Simulates a single key press (e.g., `'Enter'`, `'Control+C'`). |
| `locator.press_sequentially(text)` | Simulates typing character by character. |
| `locator.check()` | Checks a checkbox or radio button. |
| `locator.uncheck()` | Unchecks a checkbox. |
| `locator.set_checked(checked: bool)` | Sets the checked state of a checkbox or radio. |
| `locator.select_option(...)` | Selects one or more options in a `<select>`. Accepts value, label, or index. |
| `locator.hover()` | Hovers over an element. |
| `locator.focus()` | Focuses an element. |
| `locator.set_input_files(...)` | Sets files for a file input. Accepts a path, list of paths, or file payload `{'name': str, 'mimeType': str, 'buffer': bytes}`. |
| `locator.drag_to(target)` | Drags an element to another. |
| `locator.scroll_into_view_if_needed()`| Scrolls an element into view. |

---

## Assertions

Playwright's `expect` function creates assertions that auto-retry until a timeout is reached.

- **Global Timeout**: `expect.set_options(timeout=ms)`
- **Per-Assertion Timeout**: `expect(locator).to_be_visible(timeout=ms)`
- **Custom Message**: `expect(locator, "custom error message").to_...()`

### Locator Assertions: `expect(locator)...`

- `.to_be_visible()` / `.to_be_hidden()`
- `.to_be_enabled()` / `.to_be_disabled()`
- `.to_be_checked()` / `.to_be_checked(checked=False)`
- `.to_be_editable()`
- `.to_be_empty()`
- `.to_be_focused()`
- `.to_have_text(text|re|list[str])`
- `.to_contain_text(text|re|list[str])`
- `.to_have_attribute(name, value|re)`
- `.to_have_class(class|re|list[str])`
- `.to_have_count(count)`
- `.to_have_css(name, value|re)`
- `.to_have_id(id)`
- `.to_have_value(value|re)`
- `.to_have_values(list[str|re])` (for `<select multiple>`)
- `.to_be_in_viewport()`

### Page Assertions: `expect(page)...`

- `.to_have_title(title|re)`
- `.to_have_url(url|re)`

### API Response Assertions: `expect(response)...`

- `.to_be_ok()`

---

## Events, Dialogs, and New Pages

### Waiting for Events (Context Managers)

```python
# Wait for a new page/tab to open after an action
with page.expect_popup() as popup_info:
    page.get_by_text("Open Popup").click()
new_page = popup_info.value

# Wait for a network response
with page.expect_response("**/api/data") as response_info:
    page.get_by_text("Fetch Data").click()
response = response_info.value

# Wait for a file download
with page.expect_download() as download_info:
    page.get_by_text("Download File").click()
download = download_info.value
download.save_as("file.zip")
```
- Also available: `expect_request`, `expect_file_chooser`, `expect_console_message`.

### Event Listeners

- `page.on(event, handler)` / `page.once(event, handler)` / `page.remove_listener(event, handler)`
- Common events: `"request"`, `"response"`, `"console"`, `"dialog"`, `"popup"`, `"websocket"`.

### Dialogs (`alert`, `confirm`, `prompt`)

- **Gotcha**: If a listener is registered for the `"dialog"` event, it **must** handle the dialog by calling `dialog.accept()` or `dialog.dismiss()`, otherwise the test will hang. Dialogs are auto-dismissed if no listener is present.
- `page.on("dialog", handler)`: The handler receives a `dialog` object.
- `dialog.accept(prompt_text=None)`: Accepts the dialog.
- `dialog.dismiss()`: Dismisses the dialog.

---

## Network Control

### Routing & Mocking

Set up request interception on a `page` or `context`. The handler function receives a `Route` object.

- `page.route(url_glob_or_regex, handler)`

**Route Handler Actions**:
- `route.fulfill(status, headers, body, json, path)`: Respond with a mock response.
- `route.abort(error_code='failed')`: Block the request.
- `route.continue_(headers, method, post_data, url)`: Modify the request and let it proceed.
- `route.fetch()`: Fetch the real response to modify it before fulfilling.

```python
# Example: Mock an API call
def handle_route(route):
    route.fulfill(json={"data": "mocked_data"})

page.route("**/api/user", handle_route)
```

### HTTP Authentication & Proxies

These are configured on the `BrowserContext` or at browser launch.
- **Auth**: `browser.new_context(http_credentials={'username': 'u', 'password': 'p'})`
- **Proxy**: `browser.launch(proxy={'server': 'http://...'})`

---

## JavaScript & Handles

**`Locator` vs. `ElementHandle`**: Always prefer `Locator`. `ElementHandle` points to a specific DOM node which can become stale. Use handles only when absolutely necessary (e.g., passing an element to a 3rd-party library).

### Evaluation

Execute JavaScript in the page's context. Pass arguments from Python to JS safely.

- `page.evaluate(js_function_str, arg=None)`: Returns a serializable result from the page.
- `locator.evaluate(js_function_str, arg=None)`: Same, but passes the located element as the first argument to the JS function.
- `page.add_init_script(script=str, path=str)`: Injects script before any page scripts run.

```python
# Get the page's href
href = page.evaluate("() => document.location.href")

# Pass data to the page
element_text = locator.evaluate("el => el.textContent", locator)
```

### Handles (Use with Caution)

- `locator.element_handle()`: Get an `ElementHandle` for a locator.
- `page.evaluate_handle(js_function_str)`: Get a `JSHandle` (a reference to a JS object in the page).
- `handle.dispose()`: Release the handle to prevent memory leaks.

