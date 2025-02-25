function chat_user_script() {
	Object.assign(SHORTCUTS_MESSAGE, shortcuts_to_dict([
    ['shift+enter', send_random_message, 'Send a random message'],
    ['alt+enter', poke, 'Poke the chat'],
  ]));
}
