"""Tests for login functionality."""

from playwright.sync_api import Page, expect

def test_login(allychat: Page):
    """Test that login succeeded"""
    input_field = allychat.locator("#content")
    expect(input_field).to_be_visible()
