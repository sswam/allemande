"""End-to-end tests for the chat interface"""

import re

from playwright.sync_api import Page


def test_send_message(allychat: Page, auth_credentials: dict):
    """Test sending a message and receiving a response from Ally"""
    creds = auth_credentials

    screen_name = creds["username"].title()
    agent_name = "Ally"

    # Handle iframe for messages
    messages_frame = allychat.frame_locator("#messages_iframe")

    # Press mod buttons and handle possible confirm dialog
    # allychat.click("#mod")
    # allychat.once("dialog", lambda dialog: dialog.accept())
    # allychat.click("#mod_clear")
    # allychat.click("#mod_cancel")

    # Send test message
    test_message = f"{agent_name}, hello from {screen_name} at Testalot, our automated test system!"
    allychat.fill("#content", test_message)
    allychat.click("#send")

    # Wait for message to appear in iframe
    sent_msg = messages_frame.locator(f'.message[user="{screen_name}"] .content:has-text("{test_message}")').last
    sent_msg.wait_for(state="visible", timeout=3000)

    messages_frame.wait_for_function(f"""
        () => {{
            const messages = document.querySelectorAll('.message');
            return messages.length > 0 && messages[messages.length - 1].getAttribute('user') === '{agent_name}';
        }}
    """, timeout=10000)

    # Verify message order
    messages = messages_frame.locator(".message").all()
    sent_index = -2  # Second to last message should be our sent message
    response_index = -1  # Last message should be the response

    assert messages[sent_index].get_attribute("user") == screen_name, "Sent message should be from the test user"
    assert messages[response_index].get_attribute("user") == agent_name, "Last message should be from the agent"

    response = messages[response_index]

    # Verify response content
    response_text = response.text_content() or ""
    response_text = re.sub(rf"^{agent_name}:", "", response_text).strip()
    assert response_text.strip() != "", "The response should not be empty"
