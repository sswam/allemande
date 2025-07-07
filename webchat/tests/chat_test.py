"""End-to-end tests for the chat interface"""

import re

import pytest
from playwright.sync_api import Page, expect, TimeoutError


TIMEOUT = 10000  # Default timeout for Playwright actions


@pytest.mark.parametrize("clear", [True, False], ids=["clear", "no_clear"])
def test_send_message(allychat: Page, auth_credentials: dict, clear: bool):
    """Test sending a message and receiving a response from Ally"""
    creds = auth_credentials

    screen_name = creds["username"].title()
    agent_name = "Ally"

    # Handle iframe for messages
    messages_frame = allychat.frame_locator("#messages_iframe")

    if clear:
        # Press mod buttons and handle possible confirm dialog
        allychat.click("#mod")
        allychat.once("dialog", lambda dialog: dialog.accept())
        allychat.click("#mod_clear")

        try:
            allychat.click("#mod_cancel")
        except TimeoutError:
            print("mod_cancel button was not visible")

        # Wait for messages to be cleared
        expect(messages_frame.locator('.message')).to_have_count(0, timeout=3000)

    # Send test message
    if clear:
        test_message = f"{agent_name}, hello from {screen_name} at Testalot, our automated test system!"
    else:
        test_message = f"How's it going, {agent_name}, been up to anything cool lately? *smiles*"
    allychat.fill("#content", test_message)
    allychat.click("#send")

    # Look for sent message; assuming AI is slower than playwright, which it is!
    sent = messages_frame.locator(".message").last
    expect(sent).to_have_attribute("user", screen_name, timeout=TIMEOUT)
    expect(sent).to_contain_text(test_message.replace("*", ""), timeout=TIMEOUT)

    # Look for reply
    response = messages_frame.locator(".message").last
    expect(response).to_have_attribute("user", agent_name, timeout=TIMEOUT)

    # Verify response content
    response_text = response.text_content() or ""
    response_text = re.sub(rf"^{agent_name}:", "", response_text).strip()
    assert response_text.strip() != "", "The response should not be empty"
