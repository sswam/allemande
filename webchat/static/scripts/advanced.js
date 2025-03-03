function chat_user_script() {
	Object.assign(SHORTCUTS_MESSAGE, shortcuts_to_dict([
    ['alt+enter', poke, 'Poke the chat'],
    ['alt+1', () => send_continue(), 'Send a continue message'],
    ['alt+2', () => send_continue(2), 'Send a continue message to 2nd-last speaker'],
    ['alt+3', () => send_continue(3), 'Send a continue message to 3rd-last speaker'],
    ['alt+4', () => send_continue(4), 'Send a continue message to 4th-last speaker'],
    ['alt+5', () => send_continue(5), 'Send a continue message to 5th-last speaker'],
    ['alt+6', () => send_continue(6), 'Send a continue message to 6th-last speaker'],
    ['alt+7', () => send_continue(7), 'Send a continue message to 7th-last speaker'],
    ['alt+8', () => send_continue(8), 'Send a continue message to 8th-last speaker'],
    ['alt+9', () => send_continue(9), 'Send a continue message to 9th-last speaker'],
    ['alt+0', () => send_continue(10), 'Send a continue message to 10th-last speaker'],
    ['shift+enter', send_random_message, 'Send a random message'],
  ]));
}
