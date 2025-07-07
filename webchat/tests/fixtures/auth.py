"""Authentication fixtures for testing."""

import os
import pytest
from playwright.sync_api import Page, expect


DEFAULT_ROOM = "Ally Chat"


@pytest.fixture(scope="session")
def auth_credentials():
    """Get SFW authentication credentials."""
    username = os.environ["ALLEMANDE_TEST_USER"]
    password = os.environ["ALLEMANDE_TEST_PASSWORD"]
    site_url = os.environ["ALLEMANDE_SITE_URL"]
    return {"username": username, "password": password, "site_url": site_url}


@pytest.fixture(scope="session")
def auth_credentials_nsfw():
    """Get NSFW authentication credentials."""
    username = os.environ["ALLEMANDE_TEST_NSFW_USER"]
    password = os.environ["ALLEMANDE_TEST_NSFW_PASSWORD"]
    site_url = os.environ["ALLEMANDE_SITE_URL"]
    return {"username": username, "password": password, "site_url": site_url}


@pytest.fixture
def allychat(
    page: Page,
    request,
    auth_credentials,
    auth_credentials_nsfw
) -> Page:
    """
    Create an authenticated browser session.

    This fixture is configured via indirect parametrization. A test should use:
    @pytest.mark.parametrize(
        "allychat",
        [{"nsfw": False, "room": "some_room"}],
        indirect=True
    )
    """
    # Default configuration if no parameters are passed
    config = {"nsfw": False, "room": None}

    if hasattr(request, "param"):
        config.update(request.param)

    nsfw = config["nsfw"]
    room = config["room"]

    creds = auth_credentials_nsfw if nsfw else auth_credentials

    # Go to the test user's public room if no room is specified
    if room is None:
        room = creds["username"]

    # login
    page.goto(creds["site_url"])
    page.fill("#username", creds["username"])
    page.fill("#password", creds["password"])
    page.click("#login")

    # check if login was successful
    room_input = page.locator("#room")
    room_input.wait_for(state="visible")

    # check if we are in the default room
    expect(room_input).to_have_value(DEFAULT_ROOM)

    # if a specific room is provided, go to that room
    if room not in ["", DEFAULT_ROOM]:
        room_input.fill(room)
        room_input.press("Enter")

    yield page

    # Handle potential confirm dialog during logout
    page.once("dialog", lambda dialog: dialog.accept())

    page.click("#logout")
    page.wait_for_url(creds["site_url"])
    page.locator("#username").wait_for(state="visible")
    page.locator("#password").wait_for(state="visible")
