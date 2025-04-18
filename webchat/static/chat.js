const ROOMS_URL =
  location.protocol + "//" + location.host.replace(/^chat\b/, "rooms");
const SITE_URL =
  location.protocol + "//" + location.host.replace(/^.*?\./, "") + "/";
const MAX_ROOM_NUMBER = 1e3; // 1e12;
const DEFAULT_ROOM = "Ally Chat";
const EXTENSION = ".bb";

const $head = $("head");
const $body = $("body");
const $room = $id("room");
const $content = $id("content");
const $math_input = $id("math_input");
const $messages_iframe = $id("messages_iframe");
const $form = $id("form");
const $title = $("title");
const $inputrow = $id("inputrow");
const $edit = $id("view_edit");
const $auto = $id('mod_auto');
const $messages_overlay = $id("messages_overlay");

let is_private = false;
let access_denied = false;

const narrator = "Nova";
const illustrator = "Illu";

const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

let lastMessageId = null;

let view_options = {
  ids: 0,
  images: 1,
  alt: 0,
  source: 1,
  details: 0,
  canvas: 0,
  clean: 0,
  columns: 0,
  compact: 0,
  history: 0,
  image_size: 4,
  font_size: 4,
  input_row_height: 72,
  theme: "pastel",
  details_changed: true,
  highlight: 1,
  highlight_theme_light: "a11y-light",
  highlight_theme_dark: "a11y-dark",
  fullscreen: 0,
  advanced: 0,
  audio_stt: 0,
  audio_tts: 0,
  audio_vad: 0,
  audio_auto: 0,
  audio_voice: "ballad",
};

let tts_voice_options = [
  'alloy',
  'ash',
  'ballad',
  'coral',
  'echo',
  'fable',
  'nova',
  'onyx',
  'sage',
  'shimmer',
];

let view_image_size_delta = 1;
let view_font_size_delta = 1;


// simple messages to keep the conversation going
const random_message = [
  "ok",
  "okay",
  "sure",
  "yes",
  "Okay",
  "I see",
  "I understand",
  "I agree",
  "that's right",
  "that's true",
  "I know",
  "that's interesting",
  "I like that",
  "I love that",
  "what happened next?",
  "I'm listening",
  "tell me more",
  "*listens*",
  "*nods*",
  "*smiles*",
  "go on",
  "and then?",
  "what happened?",
  "what's next?",
  "wow",
  "please continue",
  "tell me more",
]

let VERSION;
let DEBUG = true;

let room;
let user;
let admin = false;
let dev = false;
let controls = "input_main";
let top_controls = "top_main";
let view = "messages";

let room_ready = false;
let theme;
let last_users = [];

const ADMIN = "admin";

// developer functions -------------------------------------------------------

const real_console_log = console.log;

function set_debug(debug) {
  DEBUG = debug;
  console.log = DEBUG ? real_console_log : () => {};
  active_set("debug", DEBUG);
}

function setup_dev() {
  dev = DEVS.includes(user);
  if (dev) {
    show($id("debug"));
    $on($id("debug"), "click", () => set_debug(!DEBUG));
  } else {
    DEBUG = false;
  }
}

// send a message ------------------------------------------------------------

function set_content(content, allow_undo) {
  if (allow_undo) {
    $content.setRangeText(content, 0, $content.value.length, 'end');
  } else {
    $content.value = content;
  }
  message_changed();
}

async function send_form_data(formData) {
  active_inc("send");

  const response = await fetch("/x/post", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("send failed");
  }

  const data = await response.json();

  if (data.error) {
    throw new Error(data.error);
  }

  return data;
}

async function send(ev) {
  if (ev)
    ev.preventDefault();

  auto_play_back_off();

  // if shift or ctrl is pressed, change the active count
  // TODO this is weird, especially adding to it, maybe don't?  Just shift-click could clear it.
  // could be useful to block auto-play though... ???
  if (ev && ev.shiftKey)
    return active_inc("send");
  if (ev && ev.ctrlKey)
    return active_dec("send");

  // if alt is pressed, send an empty message (poke)
  if (ev && ev.altKey)
    return await poke();

  const formData = new FormData($form);
  const message = $content.value;
  set_content("");

  try {
    await send_form_data(formData);
  } catch (err) {
    console.error(err.message);
    set_content(message);
    error("send");
  }

  $content.placeholder = "";
}

async function send_text(text) {
  const formData = new FormData();
  formData.append("room", $room.value);
  formData.append("content", text);
  await send_form_data(formData);
}

async function poke(ev) {
  if (ev)
    ev.preventDefault();
  await send_text("");
}

function clear_content(ev) {
  if (ev)
    ev.preventDefault();
  set_content("");
}

function focus_content() {
  // console.log("focus_content");
  $content.focus();
}

export async function send_random_message() {
  const message = random_message[Math.floor(Math.random() * random_message.length)];
  await send_text(message);
}

export async function send_continue(n) {
  // nth from the end of the last_users array
  n = n || 1;
  if (n > last_users.length) return;
  // console.log("send_continue", n);
  // console.log("last_users", last_users);
  const message = "-@" + last_users[last_users.length - n];
  // console.log("message", message);
  await send_text(message);
}


// error indicator for buttons -----------------------------------------------

async function flash($el, className) {
  $el.classList.add(className);
  await $wait(300);
  $el.classList.remove(className);
}

async function error(id) {
  const $e = $id(id);
  if (!$e)
    return;
  await flash($e, "error");
}

// active indicator for buttons ----------------------------------------------

const active_counts = {};
const active_max_class = 20;

function active_get(id) {
  let count = active_counts[id] || 0;
  if (!count && $id(id).classList.contains("active")) {
    count = active_counts[id] = count = 1;
  }
  return count;
}

function active_set(id, new_count) {
  if (new_count === undefined) {
    new_count = 1;
  }
  new_count = +new_count;
  let count = active_get(id);
  const $el = $id(id);
  if (count != 0)
    $el.classList.remove(`active-${Math.min(count, active_max_class)}`);
  count = active_counts[id] = new_count;
  if (count == 0) {
    $el.classList.remove("active");
  } else {
    $el.classList.add("active");
    $el.classList.add(`active-${Math.min(count, active_max_class)}`);
  }
}

function active_add(id, delta, max) {
  let count = active_get(id) + delta;
  if (max !== undefined) {
    count = Math.min(count, max);
  }
  // constrains > 0 for now
  count = Math.max(count, 0);
  active_set(id, count);
}

function active_inc(id, max) {
  active_add(id, 1, max);
}

function active_dec(id) {
  active_add(id, -1);
}

function active_reset(id) {
  active_set(id, 0);
}

function active_toggle(id) {
  const active = active_get(id) ? 0 : 1;
  active_set(id, active);
  return active;
}

// new chat message ----------------------------------------------------------

function new_chat_message(message) {
  auto_play_back_off();
  const message_user_lc = message.user?.toLowerCase();
  // console.log("new message user vs user", message_user_lc, user);
  if (message_user_lc != user) {
    active_dec("send");
    if (message.user) {
      // This doesn't quite work right, perhaps we don't receive the messages in order?
      // console.log("adding to last users", message.user, last_users);
      // remove any existing entry
      last_users = last_users.filter(u => u != message.user);
      last_users.push(message.user);
      if (last_users.length > 10)
        last_users.shift();
    }
  }
  lastMessageId = message.lastMessageId;
}

// insert tabs and indent ----------------------------------------------------

function content_insert_tab(ev) {
  textarea_indent($content, ev.shiftKey);
}

function edit_indent(ev) {
  textarea_indent($edit, ev.shiftKey);
}

function edit_dedent(ev) {
  textarea_indent($edit, true);
}

function textarea_indent(textarea, dedent = false) {
  // If no selection, handle single tab insertion/removal
  textarea.focus();
  if (textarea.selectionStart === textarea.selectionEnd) {
    // console.log("single tab");
    if (dedent) {
      // For shift-tab with no selection, remove previous tab if it exists  // FIXME not ideal
      const pos = textarea.selectionStart;
      if (pos > 0 && textarea.value[pos - 1] === '\t') {
        setRangeText(textarea, '', pos - 1, pos);
        textarea.selectionStart = textarea.selectionEnd = pos - 1;
      }
    } else {
      // For tab with no selection, insert a tab at caret
      setRangeText(textarea, '\t', textarea.selectionStart, textarea.selectionEnd);
      const newPos = textarea.selectionStart + 1;
      textarea.selectionStart = textarea.selectionEnd = newPos;
    }
    return;
  }

  // Save initial selection
  const selStart = textarea.selectionStart;
  const selEnd = textarea.selectionEnd;

  // Get the text content
  const text = textarea.value;

  // Find start of first line
  let blockStart = selStart;
  while (blockStart > 0 && text[blockStart - 1] !== '\n') {
    blockStart--;
  }

  // Find end of last line
  let blockEnd = selEnd;
  while (blockEnd < text.length && text[blockEnd] !== '\n') {
    blockEnd++;
  }
  // Do not include the trailing newline

  // Split the selected block into lines
  const selectedText = text.slice(blockStart, blockEnd);
  const lines = selectedText.split('\n');

  // Process each line
  const processedLines = [];
  if (dedent) {
    // Remove one tab if it exists at the start
    for (const line of lines) {
      if (line.startsWith('\t')) {
        processedLines.push(line.slice(1));
      } else if (line.startsWith('    ')) {
        processedLines.push(line.slice(4));
      } else if (line.startsWith('  ')) {
        processedLines.push(line.slice(2));
      } else if (line.startsWith(' ')) {
        processedLines.push(line.slice(1));
      } else {
        processedLines.push(line);
      }
    }
  } else {
    for (const line of lines) {
      // Add a tab
      processedLines.push('\t' + line);
    }
  }

  // Join the lines back together
  const newText = processedLines.join('\n');

  // Replace the text
  setRangeText(textarea, newText, blockStart, blockEnd);

  // Calculate new selection positions
  const deltaLength = newText.length - (blockEnd - blockStart);
  const newSelStart = selStart + (selStart > blockStart ? deltaLength : 0);
  const newSelEnd = selEnd + deltaLength;

  // Restore selection
  textarea.setSelectionRange(newSelStart, newSelEnd);
}

function setRangeText(textarea, newText, blockStart, blockEnd) {
  textarea.focus();

  // Store original selection
  const selStart = textarea.selectionStart;
  const selEnd = textarea.selectionEnd;

  // console.log(selStart, selEnd);

  // Make the replacement
  textarea.setSelectionRange(blockStart, blockEnd);
  const oldText = textarea.value.slice(blockStart, blockEnd);
  document.execCommand('insertText', false, newText);

  // Calculate how the replacement affected positions
  const lengthDiff = newText.length - (blockEnd - blockStart);

//   console.log(oldText, newText);
//   console.log(oldText.length, newText.length);
//   console.log(lengthDiff);

  // Restore selection, adjusting for text length changes
  const adjustedStart = selStart < blockStart ? selStart :
            selStart > blockEnd ? selStart + lengthDiff :
            blockEnd + lengthDiff;

  const adjustedEnd = selEnd < blockStart ? selEnd :
            selEnd > blockEnd ? selEnd + lengthDiff :
            blockEnd + lengthDiff;

//   console.log(selStart, selEnd);
//   console.log(blockStart, blockEnd);
//   console.log(adjustedStart, adjustedEnd);

  textarea.setSelectionRange(adjustedStart, adjustedEnd);
}

// handle message change -----------------------------------------------------

function message_changed(ev) {
  const $send = $id("send");
  if ($content.value == "") {
    $send.innerHTML = icons["poke"];
    $send.title = "poke the chat: alt+enter";
  } else {
    $send.innerHTML = icons["send"];
    $send.title = "send your message: ctrl+enter";
  }
}

function content_keydown(ev) {
  auto_play_back_off();
}

// change room ---------------------------------------------------------------

function messages_iframe_set_src(url) {
  $messages_iframe.contentWindow.location.replace(url);
  room_ready = false;
}

function reload_messages() {
  reload_page();
  // because the following does not work reliably...
  // clear_messages_box();
  // setTimeout(() => set_room(), 1);
}

function clear_messages_box() {
  messages_iframe_set_src("about:blank");
}

function get_file_type(name) {
  if (name.match(/\/$/))             // ends with /
    return "dir";
  else if (name.match(/\.[^\/]*$/))  // has an extension
    return "file";
  else
    return "room";                   // no extension
}

async function set_room(room_new, no_history) {
  // check if room_new was passed
  if (room_new === undefined) {
    $room.value = $room.value.trim();
    room_new = $room.value;
  }

  // check if we're already in the room
  if (room === room_new) {
    // console.log("already in room", room);
    active_reset("room_ops_move");
    // $content.focus();
    return;
  }

  // check if we're moving / renaming
  if (active_get("room_ops_move")) {
    if (room_new = await move(room, room_new)) {
      active_reset("room_ops_move");
      // continue browsing to the new name, will do a reload unfortunately
    } else {
      // move was rejected
      $room.value = room;
      error("room_ops_move");
      // stay in move mode
      select_room_basename();
      return;
    }
  }

  const type = get_file_type(room_new);

  if (view === "view_edit" && type == "dir" && !edit_close()) {
    // reject changing to a directory if we have unsaved changes in the editor
    $room.value = room;
    error("room");
    return;
  }

  room = $room.value = room_new;
  set_title_hash(room, no_history);

  clear_messages_box();
  if (!room) return;

  if (type == "room") {
    try {
      await get_options();  // can throw if access denied
    } catch {
      setup_all_link_buttons();
      return;
    }
  }

  //	who();

  setup_all_link_buttons();
  setup_admin();

  if (view === "view_edit") {
    editor_file = room_new;
    if (type == "room")
      editor_file += EXTENSION;
    editor_text_orig = null;
  } else if (type == "file") {
    // start editing the file
    edit(room_new);
  }

  if (view !== "view_edit")
    reset_ui();

  if (type == "room" || type == "dir") {
    messages_iframe_set_src(room_url() + "?stream=1");

    // console.log("set_room, calling check_for_updates");
    check_for_updates();
  }
}

function room_url() {
  const type = get_file_type(room);
  let url = ROOMS_URL + "/" + room;
  if (type == "room") {
    url += ".html";
  }
  return url;
}

function setup_all_link_buttons() {
  show_room_privacy();
  setup_user_button();
  setup_nav_buttons();
}

function show_room_privacy() {
  const $privacy = $id("privacy");
  is_private = room.startsWith(user + "/");
  if (access_denied) {
    $privacy.innerHTML = icons["access_denied"];
    $privacy.title = "denied";
  } else if (is_private) {
    $privacy.innerHTML = icons["access_private"];
    $privacy.title = "private";
  } else {
    $privacy.innerHTML = icons["access_public"];
    $privacy.title = "public";
  }

  if (is_private) {
    $privacy.href = "/" + query_to_hash(DEFAULT_ROOM);
  } else {
    $privacy.href = "/" + query_to_hash(user + "/chat");
  }
}

// move a room or file -----------------------------------------------------

function move_mode() {
  // button was clicked, toggle move mode
  if (active_toggle("room_ops_move")) {
    select_room_basename();
  } else {
    // $content.focus();
  }
}

async function move(source, dest) {
  const source_type = get_file_type(source);
  if (source_type == "dir" && !dest.match(/\/$/))
    dest += "/";
  if (dest.endsWith(EXTENSION)) {
    dest = dest.slice(0, -EXTENSION.length);
  }
  const dest_type = get_file_type(dest);
  if (source_type != dest_type) {
    return false;
  }

  const dest_name_to_return = dest;

  // console.log("dest_name_to_return", dest_name_to_return);

  // add extension to room names
  if (source_type == "room") {
    source += EXTENSION;
    dest += EXTENSION;
  }

  // remove trailing / from directories
  if (source_type == "dir") {
    source = source.replace(/\/$/, "");
    dest = dest.replace(/\/$/, "");
  }

  // call the server to do the move
  const formData = new FormData();
  formData.append("source", source);
  formData.append("dest", dest);

  const my_error = async (error_message) => {
    console.error(error_message);
    await error(`move`);
    return false;
  };

  const response = await fetch("/x/move", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    return await my_error("move failed");
  }
  return dest_name_to_return;
}

// copy a room, file or selection --------------------------------------------

function copy_mode() {
  // TODO
  // button was clicked, toggle copy mode
  active_toggle("room_ops_copy");
  if (active_get("room_ops_copy")) {
    select_room_basename();
  } else {
    // $content.focus();
  }
}

// navigation ----------------------------------------------------------------

function nav_up(ev) {
  let new_room;
  if (room == "/") {
    new_room = DEFAULT_ROOM;
  } else if (room.match(/\/$/)) {
    new_room = room.replace(/[^\/]*\/$/, "");
    if (new_room == "") {
      new_room = "/";
    }
  } else {
    new_room = room.replace(/[^\/]+$/, "") || "/";
  }
  set_room(new_room);
}

function scroll_home_end(ev, p) {
  ev.preventDefault();
  $messages_iframe.contentWindow.postMessage({ type: "scroll_home_end", p }, ROOMS_URL);
}

function scroll_pages(ev, d) {
  ev.preventDefault();
  $messages_iframe.contentWindow.postMessage({ type: "scroll_pages", d }, ROOMS_URL);
}

// user info and settings ----------------------------------------------------

async function theme_loaded() {
  const $body = document.body;
  // console.log("theme_loaded");
  const theme_mode = getComputedStyle(document.documentElement).getPropertyValue("--theme-mode");
  // console.log("theme_mode", theme_mode);
  if (theme_mode == "dark") {
    $body.classList.add("dark");
    $body.classList.remove("light");
//    $body.setAttribute("theme", "dark");
  } else {
    $body.classList.add("light");
    $body.classList.remove("dark");
//    $body.setAttribute("theme", "light");
  }
}

function load_theme() {
  const $old_link = $id("theme");
  const $new_link = $old_link.cloneNode();
  if (theme) {
    $new_link.href = "/themes/" + theme + ".css";
  } else {
    $new_link.href = "/users/" + user + "/theme.css";
  }
  $new_link.id = "theme";
  $on($new_link, "load", theme_loaded);
  $old_link.replaceWith($new_link);
}

async function load_user_styles_and_script() {
  const [_, userScript] = await Promise.all([
    $style("user_styles", "/users/" + user + "/styles.css"),
    $import("user_script", "/users/" + user + "/script.js")
  ]);

  modules.user_script = userScript;
}

// hash change ---------------------------------------------------------------

let new_hash = "";
let new_title = "";

function query_to_title(query) {
  return query;
}

function query_to_hash(query) {
  return "#" + query.replace(/ /g, "+");
}

function set_title_hash(query, no_history) {
  new_hash = query_to_hash(query);
  new_title = query_to_title(query);

  if (location.hash !== new_hash) {
    if (no_history) {
      // Replace current history entry without creating a new one
      location.replace('#' + new_hash.substring(1));
    } else {
      // Create new history entry (default behavior)
      location.hash = new_hash;
    }
  }

  $title.innerText = new_title;
}

function on_hash_change() {
  $title.innerText = query_to_title(hash_to_query(location.hash));
  let h = location.hash;
  if (h == "" || h == "#") {
    h = "#" + DEFAULT_ROOM;
  }
  if (h == "#-" && h != new_hash) {
    clear_messages_box();
  }
  if (h != new_hash) {
    let query = hash_to_query(h);
    $room.value = query;
    set_room();
  }
}

function hash_to_query(hash) {
  let query = hash.replace(/\+|%20/g, " ");
  if (query.length) {
    query = query.substr(1);
  }
  return query;
}

function go_home() {
  set_room(DEFAULT_ROOM);
}

function change_room() {
  if ($room === document.activeElement) {
    // check if selection covers entire input
    if ($room.selectionStart === 0 && $room.selectionEnd === $room.value.length) {
      go_home();
    } else {
      // select the entire input
      $room.select();
    }
  } else {
    select_room_basename();
  }
  return false;
}

function select_room_basename() {
  $room.focus();
  const value = $room.value;
  const lastSlashIndex = value.lastIndexOf('/');

  let start = 0;
  if (value.endsWith('/')) {
    // If ends with /, find the previous slash
    const previousSlashIndex = value.lastIndexOf('/', lastSlashIndex - 1);
    if (previousSlashIndex !== -1) {
      // If there's a previous slash, select from there to end
      start = previousSlashIndex + 1;
    }
  } else if (lastSlashIndex !== -1) {
    // If there's a slash (not at the end), select from after it to end
    start = lastSlashIndex + 1;
  }
  $room.setSelectionRange(start, value.length);
}

function escape() {
  if (active_get("add_math"))
    return;

  set_fullscreen(0);

  // escape from the full-screen canvas!
  if (view_options.canvas > 0) {
    view_options.canvas--;
    view_options_apply();
    return;
  }

  let acted = false;
  if (active_get("room_ops_move")) {
    $room.value = room;
    active_reset("room_ops_move");
    // $content.focus();
    acted = true;
  }
  if (controls !== "input_main") {
    set_top_left();
    set_top();
    set_controls();
    set_view();
    acted = true;
  }
  if (!acted) {
    change_room();
  }
}

// room numbers --------------------------------------------------------------

function room_set_number(n) {
  let new_room;
  if (n === "") {
    new_room = room.replace(/-?\d+$/, "");
    return new_room;
  }
  if (n < 0) {
    n = 0;
  }
  if (n > MAX_ROOM_NUMBER) {
    n = MAX_ROOM_NUMBER;
  }
  new_room = room.replace(/-?\d+$|$/, "-" + n);
  return new_room;
}

function room_get_number() {
  const match = room.match(/(\d+)$/);
  return match ? match[1] : null;
}

/*
function room_random() {
  room_set_number(Math.floor(Math.random() * (MAX_ROOM_NUMBER + 1)));
}
*/

function room_next() {
  let num = room_get_number();
  if (num === null) {
    num = 0;
  } else {
    num = +num + 1;
  }
  return room_set_number(num);
}

function room_prev() {
  let num = room_get_number();
  if (num === "0") {
    return room_set_number("");
  } else if (num === null) {
    return;
  } else {
    num = +num - 1;
  }
  return room_set_number(num);
}

function room_first() {
  return room_set_number("");
}

async function room_last(i) {
  i = i || 0;
  // fetch the last number from the server
  const room_enc = encodeURIComponent(room);
  const response = await fetch(`/x/last?room=${room_enc}`);
  if (!response.ok) {
    throw new Error("GET themes request failed");
  }
  const data = await response.json();
  if (data.error) {
    throw new Error(data.error);
  }
  // console.log("last", data.last);
  return room_set_number(+data.last + i);
}

// Keyboard shortcuts --------------------------------------------------------

export const shortcuts = {
  global: {},
  message: {},
  room: {},
  edit: {},
};

function shortcuts_to_dict(shortcuts) {
  const dict = {};
  for (const [key, fn, desc, admin] of shortcuts) {
    dict[key] = { fn, desc, admin };
  }
  return dict;
}

export function add_shortcuts(shortcuts, shortcuts_list) {
  Object.assign(shortcuts, shortcuts_to_dict(shortcuts_list));
}

function dispatch_shortcut(ev, shortcuts) {
  const key = ev.key.toLowerCase();
  const combo = [
    ev.ctrlKey ? 'ctrl+' : '',
    ev.shiftKey ? 'shift+' : '',
    ev.altKey ? 'alt+' : '',
    ev.metaKey ? 'meta+' : '',
    key,
  ].join('');

  const shortcut = shortcuts[combo];

  if (shortcut?.admin && !admin) {
    return false;
  }

  if (shortcut) {
    ev.preventDefault();
    shortcut.fn(ev);
    return true;
  }
  return false;
}

add_shortcuts(shortcuts.global, [
  ['escape', escape, 'Go back, change or leave room'],
  ['ctrl+;', change_room, 'Change room'],
  ["ctrl+[", room_first, "Go to first room"],
  ['ctrl+.', room_next, 'Go to next room'],
  ['ctrl+,', room_prev, 'Go to previous room'],
  ['ctrl+]', () => room_last(), 'Go to last room'],
  ['ctrl+\\', () => room_last(1), 'Go beyond last room'],
]);

add_shortcuts(shortcuts.message, [
  ['ctrl+enter', () => send(), 'Send message'],
  ['alt+enter', poke, 'Poke the chat'],
  ['alt+s', send, 'Send message'],
  ['alt+p', poke, 'Poke the chat'],
  ['alt+t', content_insert_tab, 'Insert tab'],
  ['shift+alt+t', content_insert_tab, 'Insert tab'],
  ['alt+backspace', clear_content, 'Clear content'],
  ['alt+u', nav_up, 'Browse up'],
  ['alt+i', view_images, 'View images'],
  ['alt+a', view_alt, 'View alt text'],
  ['alt+c', view_clean, 'View clean'],
  ['alt+j', view_canvas, 'View canvas'],
  ['alt+f', view_fullscreen, 'View fullscreen'],
  ['alt+m', add_math, 'Add math'],
  ['shift+alt+m', move_mode, 'Move mode', ADMIN],

  ['alt+z', undo, 'Undo last message', ADMIN],
  ['ctrl+alt+z', (ev) => undo(ev, true), 'Erase last message', ADMIN],
  ['alt+r', retry, 'Retry last action', ADMIN],
  ['ctrl+alt+r', (ev) => retry(ev, true), 'Retry last action', ADMIN],
  ['alt+x', clear_chat, 'Clear messages', ADMIN],
  ['shift+alt+a', archive_chat, 'Archive chat', ADMIN],
  ['shift+alt+c', clean_chat, 'Clean up the room', ADMIN],
  ['alt+e', () => edit(), 'Edit file', ADMIN],
  ['alt+h', rerender_html, 'Re-render HTML', ADMIN],

  ['alt+n', () => invoke(narrator), 'Invoke the narrator'],
  ['alt+v', () => invoke(illustrator), 'Invoke the illustrator'],
  ['alt+/', () => invoke("anyone"), 'Invoke anyone randomly'],
  ['shift+alt+/', () => invoke("everyone"), 'Invoke everyone'],
]);

add_shortcuts(shortcuts.room, [
  ['enter', focus_content, 'Focus message input'],
  ['shift+alt+m', move_mode, 'Move mode', ADMIN],
]);

add_shortcuts(shortcuts.edit, [
  ['alt+t', edit_indent, 'Insert tab / indent'],
  ['shift+alt+t', edit_dedent, 'dedent'],
  ['escape', edit_close, 'Close edit'],
  ['ctrl+s', edit_save, 'Save edit'],
  ['ctrl+enter', edit_save_and_close, 'Save edit and close'],
  ['alt+z', edit_reset, 'Reset edit'],
  ['alt+x', edit_clear, 'Clear edit'],
]);

// handle messages from the messages iframe ----------------------------------

function handle_message(ev) {
  if (ev.origin != ROOMS_URL) {
    console.error("ignoring message from", ev.origin);
    return;
  }

  if (ev.data.type == "go_home") {
    go_home();
    return;
  }

  if (ev.data.type == "new_message") {
    new_chat_message(ev.data.message);
    return;
  }

  // console.log("chat handle_message", ev.data);

  if (ev.data.type == "ready" && !room_ready) {
    // console.log("room ready");
    room_ready = true;
    theme = ev.data.theme;
    run_hooks("room_ready");
    return;
  }

  if (ev.data.type == "overlay") {
    set_overlay(ev.data.overlay);
    return;
  }

  if (ev.data.type == "copy") {
    // copy to clipboard
    try {
      navigator.clipboard.writeText(ev.data.text);
    }
    catch (err) {
      console.error("copy failed", err);
      // TODO ideally indicate to user via copy button in iframe
    }
    return;
  }

  /*
  if (ev.data.type == "size_change") {
    console.log("size_change", ev.data);
    document.documentElement.style.setProperty("--messages-width", ev.data.width + "px");
    document.documentElement.style.setProperty("--messages-height", ev.data.height + "px");
  }
  */

  // console.log("focus_content from handle_message: ev.data", ev.data);
  $content.focus();

  // detect F5 or ctrl-R to reload the page
  if (
    ev.data.type == "keydown" &&
    (ev.data.key == "F5" ||
      (ev.data.ctrlKey && ev.data.key.toLowerCase() == "r"))
  ) {
    return reload_page();
  }

  // sending on the event cannot enter text in the input,
  // but it's useful for other events we handle such as ctrl-.
  ev.data.view = window;
  ev.data.bubbles = true;
  ev.data.cancelable = true;

  if (ev.data.type == "keypress" || ev.data.type == "keydown") {
    // can we simulate this same keypress on this document?
    // ev.data.key, ev.data.ctrlKey, ev.data.altKey, ev.data.shiftKey;
    const okay = $content.dispatchEvent(
      new KeyboardEvent(ev.data.type, ev.data)
    );
  }
}

function set_overlay(overlay) {
  // set the iframe to fill the window
  if (overlay) {
    $messages_iframe.classList.add("overlay");
  } else {
    $messages_iframe.classList.remove("overlay");
  }
}

// authentication ------------------------------------------------------------

function logout_confirm(ev) {
  ev.preventDefault();
  if (confirm("Log out?"))
    logoutChat();
}

function go_to_main_site() {
    if (document.referrer == SITE_URL) {
        history.back();
    } else {
        window.location.replace(SITE_URL);
    }
}

async function authChat() {
  await $script("auth", ALLEMANDE_LOGIN_URL + "/auth.js");
  $on($id("logout"), "click", logout_confirm);
  userData = getJSONCookie("user_data");
  if (!userData) {
    // console.log("going back to main site");
    go_to_main_site();
    throw new Error("Setup error: Not logged in");
  }
  return userData.username;
}

// set the user button text and href -----------------------------------------

function setup_user_button() {
  const $user = $id("user");
  $user.innerText = user;
  // go from public user chat to default room
  if (room == user) $user.href = "/" + query_to_hash(DEFAULT_ROOM);
  // fo from users's folder to user's public room
  else if (room == user + "/") $user.href = "/" + query_to_hash(user);
  // go from private user chat to user's folder
  else if (room == user + "/chat") $user.href = "/" + query_to_hash(user) + "/";
  // from anywhere else, go to private user chat
  else $user.href = "/" + query_to_hash(user) + "/chat";
}

// set the nav button href ---------------------------------------------------

async function setup_nav_buttons() {
  // Setup nav_up button ----------------------
  const $nav_up = $id("nav_up");
  let new_room;
  if (room == "/") {
    new_room = DEFAULT_ROOM;
  } else if (room.match(/\/$/)) {
    new_room = room.replace(/[^\/]*\/$/, "");
    if (new_room == "") {
      new_room = "/";
    }
  } else {
    new_room = room.replace(/[^\/]+$/, "") || "/";
  }
  $nav_up.href = "/" + query_to_hash(new_room);

  // Setup allychat button --------------------
  const $nav_allychat = $id("nav_allychat");
  $nav_allychat.href = "/" + query_to_hash(DEFAULT_ROOM);

  // Setup porch button --------------------
  const $nav_porch = $id("nav_porch");
  $nav_porch.href = "/" + query_to_hash(user);

  // Setup home button --------------------
  const $nav_home = $id("nav_home");
  $nav_home.href = "/" + query_to_hash(user + "/chat");

  // Setup first room button --------------------
  const $nav_first = $id("nav_first");
  const nav_first_query = room_first();
  if (nav_first_query) {
    $nav_first.href = query_to_hash(nav_first_query);
  } else {
    $nav_first.removeAttribute("href");
  }

  // Setup prev room button --------------------
  const $nav_prev = $id("nav_prev");
  const roomPrev = room_prev();
  if (roomPrev) {
    $nav_prev.href = "/" + query_to_hash(roomPrev);
  } else {
    $nav_prev.removeAttribute("href");
  }

  // Setup next room button --------------------
  const $nav_next = $id("nav_next");
  const roomNext = await room_next();
  if (roomNext) {
    $nav_next.href = "/" + query_to_hash(roomNext);
  } else {
    $nav_next.removeAttribute("href");
  }

  // Setup last room button --------------------
  const $nav_last = $id("nav_last");
  const roomLast = await room_last();
  if (roomLast) {
    $nav_last.href = "/" + query_to_hash(roomLast);
  } else {
    $nav_last.removeAttribute("href");
  }
}

// Wrapper function to initialize drag controls for the input row ------------

function resizedInputRow(height) {
  view_options.input_row_height = height;
  view_options_apply();
}

function initDragControls() {
  const resizer = new DragResizer({
    element: $inputrow,
    direction: 'up',
    overlay: $messages_overlay,
    notify: resizedInputRow,
  });

  return (e) => resizer.initDrag(e);
}

// file attachments ----------------------------------------------------------

// plan:
// 1. user clicks on the attach button
// 2. user selects a file
// 3. file is uploaded to the server
// 4. server responds with a URL
// 5. URL is inserted into the message box as markdown or HTML (link, image, audio, video)
// 6. user sends the message
// 7. server receives the message and the URL

function file_clicked() {
  $id("files").click();
}

async function files_changed(ev) {
  const files = ev.target.files;
  // clear the file input so we can upload the same file again
  await upload_files(files, true);
  ev.target.value = "";
  set_controls();
}

// upload: drag and drop, paste ----------------------------------------------

function content_dragover(event) {
  event.preventDefault();
  // Add visual feedback for drag over, e.g., change border color
  $content.classList.add("drop_target");
}

function content_dragleave(event) {
  // Remove visual feedback when drag leaves
  $content.classList.remove("drop_target");
}

function content_drop(event) {
  event.preventDefault();
  $content.classList.remove("drop_target");
  const files = event.dataTransfer.files;
  upload_files(files, true);
}

function content_paste(event) {
  const items = event.clipboardData.items;
  const files = [];
  for (const item of items) {
    if (item.kind === 'file') {
      const file = item.getAsFile();
      if (file)
        files.push(file);
    }
  }
  if (files.length > 0) {
    event.preventDefault();
    upload_files(files, true)
  }
}

async function upload_files(files, to_text) {
  // upload in parallel
  active_add("add_file", files.length);
  const promises = [];
  for (const file of files) {
    promises.push(upload_file(file, file.name, to_text));
  }

  // TODO messing with the textarea value kills undo

  // make sure the message content ends with whitespace
  if (/\S$/.test($content.value)) {
    $content.value += "\n";
  }

  // but we insert the links in order
  for (const promise of promises) {
    if (!await add_upload_file_link(promise)) {
      await error("add_file");
    }
    active_dec("add_file");
  }
}

async function add_upload_file_link(promise) {
  const data = await promise;
  if (!data)
    return false;
  const { name, url, medium, markdown } = data;

  if (/\S$/.test($content.value)) {
    $content.value += " ";
  }

  $content.value += markdown;
  message_changed();
  return true;
}

async function upload_file(file, filename, to_text) {
  // upload in the background using fetch
  const formData = new FormData();
  formData.append("room", room);
  formData.append("file", file, filename);
  formData.append("to_text", to_text);

  const response = await fetch("/x/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    return null;
  }

  const data = await response.json();

  return data;
}

// admin functions -----------------------------------------------------------

function setup_admin() {
  // if first component of room path is user's name
  // or user is a global admin, then user is an admin here
  // this includes a top-level room being the user's name
  const components = room.split("/");
  const top_dir = components[0];
  admin = GLOBAL_MODERATORS.includes(user) || top_dir == user;
  if (admin) document.body.classList.add("admin");
  else document.body.classList.remove("admin");
}

async function clear_chat(ev, op) {
  if (!op) op = "clear";

  let confirm_message = "";
  if (op === "clear")
    confirm_message = "Clear the chat?";
  else if (op === "rotate")
    confirm_message = "Save and clear the first half of the chat?";
  else if (op === "archive")
    confirm_message = "Archive the chat?  You can go to it later with ctrl-].";
  else if (op == "clean")
    confirm_message = "Clean up the room?  Removes messages from specialists.";
  else if (op == "render")
    confirm_message = null;
  // TODO it would be better to hide them from everyone, with a switch
  else
    throw new Error("invalid op: " + op);

  if (confirm_message && !confirm(confirm_message)) return;

  ev.preventDefault();
  const formData = new FormData();
  formData.append("room", room);
  formData.append("op", op);

  const my_error = async (error_message) => {
    console.error(error_message);
    await error(`mod_${op}`);
  };

  const response = await fetch("/x/clear", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    return await my_error(`${op} failed`);
  }

  const data = await response.json();

  if (data.error) {
    return await my_error(data.error);
  }

  reset_ui();
}

async function archive_chat(ev) {
  await clear_chat(ev, "archive");
}

async function rotate_chat(ev) {
  await clear_chat(ev, "rotate");
}

async function clean_chat(ev) {
  await clear_chat(ev, "clean");
}

async function rerender_html(ev) {
  await clear_chat(ev, "render");
}

async function undo_last_message(room) {
  const formData = new FormData();
  formData.append("room", room);

  const response = await fetch("/x/undo", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Undo request failed");
  }

  const data = await response.json();
  if (data.error) {
    throw new Error(data.error);
  }

  return data;
}

async function undo(ev, hard) {
  ev.preventDefault();

  hard = hard || ev.ctrlKey;
  auto_play_back_off();

  if (!(ev.key || ev.shiftKey || confirm("Undo the last message?\n(hold shift to skip this confirmation next time, or use keyboard shortcuts)")))
    return false;

  if (hard) {
    try {
      await undo_last_message(room);
      // TODO should clear immediately for other users too, not just the current user
      // reload_messages();
      return true;
    } catch (err) {
      console.error(err.message);
      await error("mod_undo");
    }
  } else {
    await send_text(`<ac rm=${lastMessageId}>`);
    return true;
  }

  return false;
}

async function retry(ev, hard) {
  try {
    if (!await undo(ev, hard))
      return;
    await $wait(100);
    await poke();
  } catch (err) {
    console.error(err.message);
    await error("retry");
  }
}

// input controls ------------------------------------------------------------

function reset_ui() {
  set_controls();
//  set_top();
//  set_top_left();
  set_view();
  active_reset("send");
  active_reset("add_file");
  active_reset("edit_save");
  stop_auto_play();
  // TODO stop any current recording
}

let view_theme_original_text;

function set_controls(id) {
  id = id || "input_main";
  const $el = $id(id);
  if ($el.classList.contains("hidden")) {
    hide($("#inputrow > .controls:not(.hidden)"));
    show($id(id));
  }
  if (id === "input_main") {
    // setTimeout(() => $content.focus(), 1);
  }
  if (id === "input_view") {
    if (view_theme_original_text) {
      $id("view_theme").textContent = view_theme_original_text;
    } else {
      view_theme_original_text = $id("view_theme").textContent;
    }
    $on($id("view_theme"), "mouseover", show_theme);
  }
  controls = id;
}

// top controls --------------------------------------------------------------

// TODO think about and combine controls functions

function set_top(id) {
  id = id || "top_main";
  const $el = $id(id);
  if ($el.classList.contains("hidden")) {
    hide($("#top > .top_controls:not(.hidden)"));
    show($el);
  }
  top_controls = id;
}

function set_top_left(id) {
  id = id || "top_left_main";
  const $el = $id(id);
  if ($el.classList.contains("hidden")) {
    hide($("#top > .top_left_controls:not(.hidden)"));
    show($el);
  }
  top_controls = id;
}

// auto play -----------------------------------------------------------------

let auto_play_interval_timer = null;
let auto_play_interval = null;
const auto_play_interval_options = [null, 1, 2, 3, 4, 5, 10, 15, 20, 25, 30, 45, 60, 90, 120, 180, 300, 600, 1200, 1800, 3600];


function fmt_duration(seconds) {
  let s = seconds % 60;
  let m = Math.floor(seconds / 60) % 60;
  let h = Math.floor(seconds / 3600);

  if (h) return `${h}h${m ? ` ${m}m` : ''}`;
  if (m) return `${m}m${s ? ` ${s}s` : ''}`;
  return `${s}s`;
}

function auto_play_poke() {
  // don't poke if we're already waiting for a response
  if (!active_get("send"))
    poke();
}

function set_auto_play(delta) {
  if (auto_play_interval_timer) {
    clearInterval(auto_play_interval_timer);
    auto_play_interval_timer = null;
  }
  const max = auto_play_interval_options.length - 1;
  active_add("mod_auto", delta, max);
  auto_play_interval = auto_play_interval_options[active_get("mod_auto")];
  if (!auto_play_interval)
    return stop_auto_play();
  auto_play_interval_timer = setInterval(auto_play_poke, auto_play_interval * 1000);
  $auto.textContent = fmt_duration(auto_play_interval);
}

function stop_auto_play() {
  if (auto_play_interval_timer)
    clearInterval(auto_play_interval_timer);
  auto_play_interval_timer = null;
  auto_play_interval = null;
  $auto.innerHTML = icons["mod_auto"];
  active_set("mod_auto", 0);
}

function auto_play(ev) {
  if (auto_play_interval && ev.shiftKey) {
    set_auto_play(1);
  } else if (auto_play_interval && ev.ctrlKey) {
    set_auto_play(-1);
  } else if (auto_play_interval) {
    stop_auto_play();
  } else {
    auto_play_poke();
    set_auto_play(auto_play_interval_options.indexOf(15));
  }
}

function auto_play_back_off() {
  // If auto-play is active, reset its timer
  if (auto_play_interval) {
    set_auto_play(0);
  }
}

// edit file -----------------------------------------------------------------

const EDITABLE_EXTENSIONS = [
  // plain text
  "bb", "m", "txt", "md", "markdown",
  // web files
  "html", "htm", "css",
  // textual data
  "json", "xml", "yaml", "yml", "ini", "cfg", "conf", "log",
  // program code
  "js", "py", "sh", "c", "rb", "lua", "ts", "make", "sql",
  // tabular data
  "csv", "tsv",
];

const DISALLOWED_EXTENSIONS = [
  // images
  "jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico", "tiff", "tif", "psd", "xcf", "eps", "ai", "indd", "eps", "svg", "svgz", "wmf", "emf",
  // audio
  "mp3", "wav", "ogg", "flac",
  // video
  "mp4", "webm", "avi", "mov", "flv", "mkv", "wmv", "m4v", "mpg", "mpeg", "3gp", "3g2", "vob", "ogv", "qt", "divx", "xvid", "rm", "rmvb", "asf", "swf",
  // non-text documents
  "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "odp", "rtf",
  // archives
  "zip", "gz", "rar", "7z", "tar", "bz2", "xz", "lz", "cab", "iso", "tgz",
  // binary executables
  "exe", "msi", "dmg", "app", "apk", "jar", "deb", "rpm", "bin", "dll", "class",
  // fonts
  "ttf", "otf", "woff", "woff2", "eot", "svg", "svgz",
  // other
  "torrent",
];

async function check_mime_type(file) {
  const response = await fetch(ROOMS_URL + "/" + file, {
    method: "HEAD",
  });
  if (!response.ok) {
    throw new Error("HEAD request failed: " + file);
  }
  const mime = response.headers.get("Content-Type");
  return mime;
}

async function check_ok_to_edit(file) {
  // don't edit folders, editing in /
  if (file.match(/\/$/)) {
    throw new Error("cannot edit folder: " + file);
  }

  const basename = file.replace(/^.*\//, "");
  const ext = basename.replace(/^.*\.|.*/, "").toLowerCase();

  if (DISALLOWED_EXTENSIONS.includes(ext)) {
    throw new Error("disallowed extension: " + ext);
  }

  const check_mime = !EDITABLE_EXTENSIONS.includes(ext);

  if (check_mime) {
    // console.log("checking mime type for file:", file);
    const mime = await check_mime_type(file);
    if (!mime.startsWith("text/")) {
      throw new Error("disallowed mime type for file: " + file + " (" + mime + ")");
    }
  }
}

async function fetch_file(file) {
  const response = await fetch(`${ROOMS_URL}/${file}?_=${Math.random()}`, {
    credentials: 'include',
    cache: 'no-cache',
  });
  if (!response.ok) {
    throw new Error("GET request failed: " + file);
  }
  const text = await response.text();

  return text;
}

async function put_file(file, text, noclobber) {
  let url = "/x/put/" + file;
  if (noclobber) {
    url += "?noclobber=1";
  }
  const response = await fetch(url, {
    method: "PUT",
    body: text,
  });
  if (!response.ok) {
    throw new Error("PUT request failed: " + file);
  }
  const data = await response.json();
  if (data.error) {
    throw new Error(data.error);
  }
  return data;
}

// TODO edit tabular data in a table, not as plain text

function set_view(id) {
  id = id || "messages";
  const $el = $id(id);
  if ($el.classList.contains("hidden")) {
    hide($(".view:not(.hidden)"));
    show($id(id));
  }
  view = id;
}

let editor_file;
let editor_text_orig;
let editor_text;
let editor_file_orig;

function edit_set_text(text) {
  $edit.value = text;
  editor_text = text;
}

function edit_get_text() {
  editor_text = $edit.value;
  return editor_text;
}

async function edit(file) {
  stop_auto_play();

  if (file === undefined) {
    file = room + EXTENSION;
  }

  try {
    check_ok_to_edit(file);
  } catch (err) {
    console.error(err.message);
    return await error("mod_edit");
  }

  editor_file = editor_file_orig = file;
  try {
    editor_text_orig = await fetch_file(file);
  } catch (err) {
    editor_text_orig = "";
    console.error(err.message);
    await error("mod_edit");
  }

  edit_set_text(editor_text_orig);
  set_view("view_edit");
  set_controls("input_edit");
  $edit.focus();
  // set caret at end
  $edit.selectionStart = $edit.selectionEnd = $edit.value.length;
}

async function edit_save() {
  if (!editor_file) {
    error("edit_save");
    return false;
  }

  edit_get_text();

  // if it's a chat room file, and not empty, ensure it ends with a double newline
  if (editor_file.endsWith(EXTENSION) && editor_text && !editor_text.match(/[^\n]\n\n$/)) {
    edit_set_text(editor_text.replace(/\n*$/, "\n\n"));
  }

  // Allow to save unchanged to force a re-render */
  /*
  if (editor_text === editor_text_orig) {
    error("edit_save");
    return false;
  }
  */

  active_inc("edit_save");

  const noclobber = editor_file !== editor_file_orig;

  try {
    await put_file(editor_file, editor_text, noclobber);
    editor_text_orig = editor_text;
  } catch (err) {
    console.error(err.message);
    await error("edit_save");
    return false;
  }

  active_dec("edit_save");
  return true;
}

async function edit_save_and_close() {
  if (await edit_save())
    edit_close();
}

function edit_reset() {
  if (edit_get_text() !== editor_text_orig) {
    if (!confirm("Discard changes?")) return;
  }
  edit_set_text(editor_text_orig);
}

function edit_clear() {
  edit_set_text("");
}

function edit_close(ev) {
  if (ev)
    ev.stopPropagation();
  if (edit_get_text() !== editor_text_orig) {
    if (!confirm("Discard changes?")) return false;
  }
  const type = get_file_type(editor_file);
  const change_to_room = type == "file" && editor_file.replace(/\.[^\/]*$/, "");
  editor_text = editor_text_orig = null;
  editor_file = null;
  $edit.value = "";
  set_view();
  set_controls();
  if (change_to_room) {
    set_room(change_to_room);
  }
  return true;
}

// view options --------------------------------------------------------------

function setup_view_options() {
  // persist from local storage JSON
  // if not present, set to default
  let view_options_str = localStorage.getItem("view_options");
  if (view_options_str) {
    const view_options_loaded = JSON.parse(view_options_str);
    for (const key in view_options_loaded) {
      view_options[key] = view_options_loaded[key];
    }
    view_options.fullscreen = 0;
  }
  add_hook("room_ready", view_options_apply);
}

function view_options_apply() {
  // includes audio options
  // save to local storage
  localStorage.setItem("view_options", JSON.stringify(view_options));
  // update buttons
  // TODO simplify / de-dup this code
  active_set("view_ids", view_options.ids);
  active_set("view_images", view_options.images);
  active_set("view_alt", view_options.alt);
  active_set("view_source", view_options.source);
  active_set("view_highlight", view_options.highlight);
  active_set("view_details", view_options.details);
  active_set("view_canvas", view_options.canvas);
  active_set("view_clean", view_options.clean);
  active_set("view_image_size", view_options.image_size - 4);
  active_set("view_font_size", view_options.font_size - 4);
  active_set("view_columns", view_options.columns);
  active_set("view_compact", view_options.compact);
  active_set("view_history", view_options.history);
  active_set("view_fullscreen", view_options.fullscreen);
  $id("view_items").value = view_options.items ?? "";
  active_set("view_advanced", view_options.advanced);
  $inputrow.style.flexBasis = view_options.input_row_height + "px";
  active_set("audio_stt", view_options.audio_stt);
  active_set("audio_tts", view_options.audio_tts);
  active_set("audio_vad", view_options.audio_vad);
  active_set("audio_auto", view_options.audio_auto);

  $id("audio_voice").value = view_options.audio_voice;

  // input placeholder in basic mode, before first message sent in this session
  let input_placeholder = "";
  if ($content.placeholder != "" && !view_options.advanced && isMobile) {
    input_placeholder = "Type your message...";
  } else if ($content.placeholder != "" && !view_options.advanced) {
    input_placeholder = "Type your message... (Ctrl+Enter to send)";
  }
  $content.placeholder = input_placeholder;

  const cl = document.body.classList;
  cl.toggle("compact", view_options.compact == 1);
  cl.toggle("simple", view_options.advanced == 0);

  if (view_options.image_size >= 10) {
    view_image_size_delta = -1;
  }
  if (view_options.image_size <= 1) {
    view_image_size_delta = 1;
  }
  const image_size_icon = view_image_size_delta > 0 ? "expand" : "contract";
  $id("view_image_size").innerHTML = icons[image_size_icon];

  if (view_options.font_size >= 10) {
    view_font_size_delta = -1;
  }
  if (view_options.font_size <= 1) {
    view_font_size_delta = 1;
  }
  const font_size_icon = view_font_size_delta > 0 ? "font_expand" : "font_contract";
  $id("view_font_size").innerHTML = icons[font_size_icon];

  const zoom = 1.15**(view_options.font_size-4);
  const font_size = Math.round(16*zoom);
  document.documentElement.style.setProperty("--font-size", font_size + "px");
  const font_size_code = 12 * Math.round(zoom);
  document.documentElement.style.setProperty("--font-size-code", font_size_code + "px");

  view_options.details_changed = false;

  if (view_options.fullscreen >= 1)
    go_fullscreen();
  else
    exit_fullscreen();

  set_overlay(view_options.fullscreen == 2);

  // send message to the rooms iframe to apply view options
  $messages_iframe.contentWindow.postMessage({ type: "set_view_options", ...view_options }, ROOMS_URL);
}

function set_fullscreen(fullscreen) {
  view_options.fullscreen = fullscreen;
  view_options_apply();
}

function fullscreenchange() {
  view_options.fullscreen = is_fullscreen() ? 1 : 0;
  view_options_apply();
}

function view_ids(ev) {
  const delta = ev.shiftKey || ev.ctrlKey ? -1 : 1;
  view_options.ids = (view_options.ids + delta + 3) % 3;
  view_options_apply();
}

function view_images(ev) {
  view_options.images = !view_options.images;
  view_options_apply();
}

function view_alt(ev) {
  view_options.alt = !view_options.alt;
  view_options_apply();
}

function view_source(ev) {
  const delta = ev.shiftKey || ev.ctrlKey ? -1 : 1;
  view_options.source = (view_options.source + delta + 3) % 3;
  view_options_apply();
}

function view_highlight(ev) {
  view_options.highlight = !view_options.highlight;
  view_options_apply();
}

function view_details(ev) {
  view_options.details = !view_options.details;
//  const delta = ev.shiftKey || ev.ctrlKey ? -1 : 1;
//  view_options.details = (view_options.details + delta + 4) % 4;
  view_options.details_changed = true;
  view_options_apply();
}

function view_canvas(ev) {
  const delta = ev.shiftKey || ev.ctrlKey ? -1 : 1;
  view_options.canvas = (view_options.canvas + delta + 3) % 3;
  view_options_apply();
}

function view_clean(ev) {
  view_options.clean = !view_options.clean;
  view_options_apply();
}

function view_columns(ev) {
  view_options.columns = !view_options.columns;
  view_options_apply();
}

function view_compact(ev) {
  view_options.compact = !view_options.compact;
  view_options_apply();
}

function view_fullscreen(ev) {
  const delta = ev.shiftKey || ev.ctrlKey ? -1 : 1;
  view_options.fullscreen = (view_options.fullscreen + delta + 3) % 3;
  view_options_apply();
}

function view_history(ev) {
  view_options.history = !view_options.history;
  view_options_apply();
}

function view_advanced(ev) {
  view_options.advanced = !view_options.advanced;
  view_options_apply();
  set_controls();
}

function clamp(num, min, max) { return Math.min(Math.max(num, min), max); }

function view_image_size(ev) {
  // starts at 4, range from 1 to 10
  const reset = ev.ctrlKey;
  if (reset) {
    view_options.image_size = 4;
    view_image_size_delta = 1;
  } else {
    const neg = ev.shiftKey ? -1 : 1;
    const delta = neg * view_image_size_delta;
    view_options.image_size = ((view_options.image_size || 4) + delta + 9) % 10 + 1;
  }
  view_options_apply();
}

function view_font_size(ev) {
  // starts at 4, range from 1 to 10
  const reset = ev.ctrlKey;
  if (reset) {
    view_options.font_size = 4;
    view_font_size_delta = 1;
  } else {
    const neg = ev.shiftKey ? -1 : 1;
    const delta = neg * view_font_size_delta;
    view_options.font_size = ((view_options.font_size || 4) + delta + 9) % 10 + 1;
  }
  view_options_apply();
}

function view_items(ev) {
  let items = ev.target.value;
  items = items === "" ? "" : +items;
  view_options.items = items;
  view_options_apply();
}

// invoke someone ------------------------------------------------------------

async function invoke(who) {
  await send_text(`-@${who}`);
}

// themes --------------------------------------------------------------------

async function fetch_themes_options() {
  const response = await fetch("/themes/");
  if (!response.ok) {
    throw new Error("GET themes request failed");
  }
  const data = await response.text();
  const parser = new DOMParser();
  const doc = parser.parseFromString(data, 'text/html');
  const links = [...doc.getElementsByTagName('a')];
  links.shift();
  const hrefs = links.map(link => link.getAttribute('href'));
  const themes_css = hrefs.filter(href => href.endsWith('.css'));
  const themes = themes_css.map(href => href.replace(/\.css$/, ''));
  return themes;
}

async function set_settings(settings) {
  const response = await fetch("/x/settings", {
    method: "POST",
    contentType: "application/json",
    body: JSON.stringify(settings),
  });

  if (!response.ok) {
    throw new Error("POST settings request failed");
  }

  const data = await response.json();
  if (data.error) {
    throw new Error(data.error);
  }

  return data;
}

async function change_theme(ev) {
  const themes = await fetch_themes_options();
  if (!themes.length) {
    return;
  }
  const index = themes.indexOf(theme);
  const mode = ev.shiftKey ? "prev" : ev.ctrlKey ? "random" : "next";
  if (mode === "next") {
    theme = themes[(index + 1) % themes.length];
  } else if (mode === "prev") {
    theme = themes[(index - 1 + themes.length) % themes.length];
  } else if (mode === "random") {
    do {
      theme = themes[Math.floor(Math.random() * themes.length)];
    } while (theme === view_options.theme && themes.length > 1);
  }
  show_theme();
  set_settings({ theme: theme });
  load_theme();
  $messages_iframe.contentWindow.postMessage({ type: "theme_changed", theme }, ROOMS_URL);
}

let hide_theme_timeout;

function hide_theme() {
  const $view_theme = $id("view_theme");
  $off($view_theme, "mouseout");
  clearTimeout(hide_theme_timeout);
  hide_theme_timeout = setTimeout(() => $view_theme.innerHTML = icons["view_theme"], 1000);
}

function show_theme() {
  const $view_theme = $id("view_theme");
  $view_theme.textContent = theme;
  $off($view_theme, "mouseout");
  $on($view_theme, "mouseout", hide_theme);
  clearTimeout(hide_theme_timeout);
}

// options -------------------------------------------------------------------

async function get_options() {
//  console.log("get_options", room);
  const query = new URLSearchParams({
    room,
  });
  const response = await fetch("/x/options?" + query, { cache: "no-cache" });
  access_denied = !response.ok;
  if (access_denied) {
    throw new Error("GET options request failed");
  }
  const data = await response.json();
//  console.log("get_options", data);

  if (data.redirect) {
    set_room(data.redirect, true);
    return;
  }

  const context = data?.agents?.all?.context ?? "";
  const lines = data?.agents?.all?.lines ?? "";
  const images = data?.agents?.all?.images ?? "";
  const mission = data?.mission === "" ? "-" : data?.mission ?? "";
  $id("opt_context").value = context;
  $id("opt_lines").value = lines;
  $id("opt_images").value = images;
  $id("opt_mission").value = mission;
  return data;
}

async function set_options(options) {
  const response = await fetch("/x/options", {
    method: "POST",
    body: JSON.stringify(options),
  });

  if (!response.ok) {
    throw new Error("POST options request failed");
  }

  const data = await response.json();
//  if (data.error) {
//    throw new Error(data.error);
//  }
}

async function opt_context(ev) {
  // console.log("opt_context", ev.target.value);
  let context = ev.target.value;
  context = context === "" ? null : +context;
  await set_options({
    room: room,
    options: {
      agents: {
        all: {
          context
        }
      }
    }
  });
}

async function opt_lines(ev) {
  let lines = ev.target.value;
  lines = lines === "" ? null : +lines;
  await set_options({
    room: room,
    options: {
      agents: {
        all: {
          lines
        }
      }
    }
  });
}

async function opt_images(ev) {
  let images = ev.target.value;
  images = images === "" ? null : +images;
  await set_options({
    room: room,
    options: {
      agents: {
        all: {
          images
        }
      }
    }
  });
}

async function opt_mission(ev) {
  let mission = ev.target.value;
  mission = mission === "" ? null : mission === "-" ? "" : mission;
  await set_options({
    room: room,
    options: {
      mission
    }
  });
}


// icons ---------------------------------------------------------------------

// This is almost like i18n!

const icons = {
  nav_up: '<svg class="icon i18 bi bi-folder-fill" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M9.828 3h3.982a2 2 0 0 1 1.992 2.181l-.637 7A2 2 0 0 1 13.174 14H2.825a2 2 0 0 1-1.991-1.819l-.637-7a2 2 0 0 1 .342-1.31L.5 3a2 2 0 0 1 2-2h3.672a2 2 0 0 1 1.414.586l.828.828A2 2 0 0 0 9.828 3m-8.322.12q.322-.119.684-.12h5.396l-.707-.707A1 1 0 0 0 6.172 2H2.5a1 1 0 0 0-1 .981z M8 6L11 9.75L5 9.75z"/></svg>',
  nav_first: '<svg class="icon i20 bi bi-skip-start-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M4 4a.5.5 0 0 1 1 0v3.248l6.267-3.636c.54-.313 1.232.066 1.232.696v7.384c0 .63-.692 1.01-1.232.697L5 8.753V12a.5.5 0 0 1-1 0z"/></svg>',
  nav_last: '<svg class="icon i20 bi bi-skip-end-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M12.5 4a.5.5 0 0 0-1 0v3.248L5.233 3.612C4.693 3.3 4 3.678 4 4.308v7.384c0 .63.692 1.01 1.233.697L11.5 8.753V12a.5.5 0 0 0 1 0z"/></svg>',
  nav_next: '<svg class="icon i20 bi bi-caret-right-fill" fill="currentColor" viewBox="0 0 16 16"><path d="m12.14 8.753-5.482 4.796c-.646.566-1.658.106-1.658-.753V3.204a1 1 0 0 1 1.659-.753l5.48 4.796a1 1 0 0 1 0 1.506z"/></svg>',
  nav_prev: '<svg class="icon i20 bi bi-caret-left-fill" fill="currentColor" viewBox="0 0 16 16"><path d="m3.86 8.753 5.482 4.796c.646.566 1.658.106 1.658-.753V3.204a1 1 0 0 0-1.659-.753l-5.48 4.796a1 1 0 0 0 0 1.506z"/></svg>',
  scroll_home: '<svg class="icon i20 bi bi-chevron-bar-up" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M3.646 11.854a.5.5 0 0 0 .708 0L8 8.207l3.646 3.647a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 0 0 0 .708M2.4 5.2c0 .22.18.4.4.4h10.4a.4.4 0 0 0 0-.8H2.8a.4.4 0 0 0-.4.4"/></svg>',
  scroll_end: '<svg class="icon i20 bi bi-chevron-bar-down" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M3.646 4.146a.5.5 0 0 1 .708 0L8 7.793l3.646-3.647a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 0-.708M1 11.5a.5.5 0 0 1 .5-.5h13a.5.5 0 0 1 0 1h-13a.5.5 0 0 1-.5-.5"/></svg>',
  scroll_pageup: '<svg class="icon i20 bi bi-chevron-up" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M7.646 4.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1-.708.708L8 5.707l-5.646 5.647a.5.5 0 0 1-.708-.708z"/></svg>',
  scroll_pagedown: '<svg class="icon i20 bi bi-chevron-down" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708"/></svg>',
  nav: '<svg class="icon i18 bi bi-compass-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M15.5 8.516a7.5 7.5 0 1 1-9.462-7.24A1 1 0 0 1 7 0h2a1 1 0 0 1 .962 1.276 7.5 7.5 0 0 1 5.538 7.24m-3.61-3.905L6.94 7.439 4.11 12.39l4.95-2.828 2.828-4.95z"/></svg>',
  logout: '<svg class="icon i20 bi bi-box-arrow-right" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M10 12.5a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-9a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v2a.5.5 0 0 0 1 0v-2A1.5 1.5 0 0 0 9.5 2h-8A1.5 1.5 0 0 0 0 3.5v9A1.5 1.5 0 0 0 1.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-2a.5.5 0 0 0-1 0z"/><path fill-rule="evenodd" d="M15.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 0 0-.708.708L14.293 7.5H5.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708z"/></svg>',
  x: '<svg class="icon i20 bi bi-x" fill="currentColor" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708"/></svg>',
  x_large: '<svg class="icon i20 bi bi-x-lg" fill="currentColor" viewBox="0 0 16 16"><path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8z"/></svg>',
  add: '<svg class="icon i20 bi bi-plus-lg" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2"/></svg>',
  view: '<svg class="icon i20 bi bi-eye-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0"/><path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8m8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7"/></svg>',
  opt: '<svg class="icon i20 bi bi-gear-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"/></svg>',
  mod: '<svg class="icon i20 bi bi-shield-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M5.072.56C6.157.265 7.31 0 8 0s1.843.265 2.928.56c1.11.3 2.229.655 2.887.87a1.54 1.54 0 0 1 1.044 1.262c.596 4.477-.787 7.795-2.465 9.99a11.8 11.8 0 0 1-2.517 2.453 7 7 0 0 1-1.048.625c-.28.132-.581.24-.829.24s-.548-.108-.829-.24a7 7 0 0 1-1.048-.625 11.8 11.8 0 0 1-2.517-2.453C1.928 10.487.545 7.169 1.141 2.692A1.54 1.54 0 0 1 2.185 1.43 63 63 0 0 1 5.072.56"/></svg>',
  send: '<svg class="icon i40 bi bi-send-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M15.964.686a.5.5 0 0 0-.65-.65L.767 5.855H.766l-.452.18a.5.5 0 0 0-.082.887l.41.26.001.002 4.995 3.178 3.178 4.995.002.002.26.41a.5.5 0 0 0 .886-.083zm-1.833 1.89L6.637 10.07l-.215-.338a.5.5 0 0 0-.154-.154l-.338-.215 7.494-7.494 1.178-.471z"/></svg>',
  poke: '<svg class="icon i40 bi bi-hand-index-thumb-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M8.5 1.75v2.716l.047-.002c.312-.012.742-.016 1.051.046.28.056.543.18.738.288.273.152.456.385.56.642l.132-.012c.312-.024.794-.038 1.158.108.37.148.689.487.88.716q.113.137.195.248h.582a2 2 0 0 1 1.99 2.199l-.272 2.715a3.5 3.5 0 0 1-.444 1.389l-1.395 2.441A1.5 1.5 0 0 1 12.42 16H6.118a1.5 1.5 0 0 1-1.342-.83l-1.215-2.43L1.07 8.589a1.517 1.517 0 0 1 2.373-1.852L5 8.293V1.75a1.75 1.75 0 0 1 3.5 0"/></svg>',
  add_file: '<svg class="icon i20 bi bi-upload" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5"/><path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708z"/></svg>',
  add_record_audio: '<svg class="icon i20 bi bi-mic-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M5 3a3 3 0 0 1 6 0v5a3 3 0 0 1-6 0z"/><path d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5"/></svg>',
  add_record_video: '<svg class="icon i20 bi bi-camera-video-fill" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M0 5a2 2 0 0 1 2-2h7.5a2 2 0 0 1 1.983 1.738l3.11-1.382A1 1 0 0 1 16 4.269v7.462a1 1 0 0 1-1.406.913l-3.111-1.382A2 2 0 0 1 9.5 13H2a2 2 0 0 1-2-2z"/></svg>',
  rec_stop: '<svg class="icon i20 bi bi-stop-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M5 3.5h6A1.5 1.5 0 0 1 12.5 5v6a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 11V5A1.5 1.5 0 0 1 5 3.5"/></svg>',
  pause: '<svg class="icon i20 bi bi-pause-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 3.5A1.5 1.5 0 0 1 7 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5m5 0A1.5 1.5 0 0 1 12 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5"/></svg>',
  view_theme: '<svg class="icon i20 bi bi-palette-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M12.433 10.07C14.133 10.585 16 11.15 16 8a8 8 0 1 0-8 8c1.996 0 1.826-1.504 1.649-3.08-.124-1.101-.252-2.237.351-2.92.465-.527 1.42-.237 2.433.07M8 5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3m4.5 3a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3M5 6.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0m.5 6.5a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3"/></svg>',
  view_images: '<svg class="icon i20 bi bi-image-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M.002 3a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-12a2 2 0 0 1-2-2zm1 9v1a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.5l-3.777-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062zm5-6.5a1.5 1.5 0 1 0-3 0 1.5 1.5 0 0 0 3 0"/></svg>',
  view_alt: '<svg class="icon i22 bi bi-alphabet" fill="currentColor" viewBox="0 0 16 16"><path d="M2.204 11.078c.767 0 1.201-.356 1.406-.737h.059V11h1.216V7.519c0-1.314-.947-1.783-2.11-1.783C1.355 5.736.75 6.42.69 7.27h1.216c.064-.323.313-.552.84-.552s.864.249.864.771v.464H2.346C1.145 7.953.5 8.568.5 9.496c0 .977.693 1.582 1.704 1.582m.42-.947c-.44 0-.845-.235-.845-.718 0-.395.269-.684.84-.684h.991v.538c0 .503-.444.864-.986.864m5.593.937c1.216 0 1.948-.869 1.948-2.31v-.702c0-1.44-.727-2.305-1.929-2.305-.742 0-1.328.347-1.499.889h-.063V3.983h-1.29V11h1.27v-.791h.064c.21.532.776.86 1.499.86Zm-.43-1.025c-.66 0-1.113-.518-1.113-1.28V8.12c0-.825.42-1.343 1.098-1.343.684 0 1.075.518 1.075 1.416v.45c0 .888-.386 1.401-1.06 1.401Zm2.834-1.328c0 1.47.87 2.378 2.305 2.378 1.416 0 2.139-.777 2.158-1.763h-1.186c-.06.425-.313.732-.933.732-.66 0-1.05-.512-1.05-1.352v-.625c0-.81.371-1.328 1.045-1.328.635 0 .879.425.918.776h1.187c-.02-.986-.787-1.806-2.14-1.806-1.41 0-2.304.918-2.304 2.338z"/></svg>',
  view_source: '<svg class="icon i20 bi bi-braces" fill="currentColor" viewBox="0 0 16 16"><path d="M2.114 8.063V7.9c1.005-.102 1.497-.615 1.497-1.6V4.503c0-1.094.39-1.538 1.354-1.538h.273V2h-.376C3.25 2 2.49 2.759 2.49 4.352v1.524c0 1.094-.376 1.456-1.49 1.456v1.299c1.114 0 1.49.362 1.49 1.456v1.524c0 1.593.759 2.352 2.372 2.352h.376v-.964h-.273c-.964 0-1.354-.444-1.354-1.538V9.663c0-.984-.492-1.497-1.497-1.6M13.886 7.9v.163c-1.005.103-1.497.616-1.497 1.6v1.798c0 1.094-.39 1.538-1.354 1.538h-.273v.964h.376c1.613 0 2.372-.759 2.372-2.352v-1.524c0-1.094.376-1.456 1.49-1.456V7.332c-1.114 0-1.49-.362-1.49-1.456V4.352C13.51 2.759 12.75 2 11.138 2h-.376v.964h.273c.964 0 1.354.444 1.354 1.538V6.3c0 .984.492 1.497 1.497 1.6"/></svg>',
  view_highlight: '<svg class="icon i16 bi bi-asterisk" fill="currentColor" viewBox="0 0 16 16"><path d="M8 0a1 1 0 0 1 1 1v5.268l4.562-2.634a1 1 0 1 1 1 1.732L10 8l4.562 2.634a1 1 0 1 1-1 1.732L9 9.732V15a1 1 0 1 1-2 0V9.732l-4.562 2.634a1 1 0 1 1-1-1.732L6 8 1.438 5.366a1 1 0 0 1 1-1.732L7 6.268V1a1 1 0 0 1 1-1"/></svg>',
//  view_highlight: '<svg class="icon i20 bi bi-braces" fill="currentColor" viewBox="0 0 16 16"><path d="M2.114 8.063V7.9c1.005-.102 1.497-.615 1.497-1.6V4.503c0-1.094.39-1.538 1.354-1.538h.273V2h-.376C3.25 2 2.49 2.759 2.49 4.352v1.524c0 1.094-.376 1.456-1.49 1.456v1.299c1.114 0 1.49.362 1.49 1.456v1.524c0 1.593.759 2.352 2.372 2.352h.376v-.964h-.273c-.964 0-1.354-.444-1.354-1.538V9.663c0-.984-.492-1.497-1.497-1.6" fill="rgba(255,0,0,0.5)"/><path d="M13.886 7.9v.163c-1.005.103-1.497.616-1.497 1.6v1.798c0 1.094-.39 1.538-1.354 1.538h-.273v.964h.376c1.613 0 2.372-.759 2.372-2.352v-1.524c0-1.094.376-1.456 1.49-1.456V7.332c-1.114 0-1.49-.362-1.49-1.456V4.352C13.51 2.759 12.75 2 11.138 2h-.376v.964h.273c.964 0 1.354.444 1.354 1.538V6.3c0 .984.492 1.497 1.497 1.6" fill="rgba(0,0,255,0.5)"/></svg>',
  view_canvas: '<svg class="icon i20 bi bi-easel-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M8.473.337a.5.5 0 0 0-.946 0L6.954 2H2a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h1.85l-1.323 3.837a.5.5 0 1 0 .946.326L4.908 11H7.5v2.5a.5.5 0 0 0 1 0V11h2.592l1.435 4.163a.5.5 0 0 0 .946-.326L12.15 11H14a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1H9.046z"/></svg>',
  view_clean: '<svg class="icon i20 bi bi-book-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783"/></svg>',
  expand: '<svg class="icon i16 bi bi-arrows-angle-expand" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M5.828 10.172a.5.5 0 0 0-.707 0l-4.096 4.096V11.5a.5.5 0 0 0-1 0v3.975a.5.5 0 0 0 .5.5H4.5a.5.5 0 0 0 0-1H1.732l4.096-4.096a.5.5 0 0 0 0-.707m4.344-4.344a.5.5 0 0 0 .707 0l4.096-4.096V4.5a.5.5 0 1 0 1 0V.525a.5.5 0 0 0-.5-.5H11.5a.5.5 0 0 0 0 1h2.768l-4.096 4.096a.5.5 0 0 0 0 .707"/></svg>',
  contract: '<svg class="icon i16 bi bi-arrows-angle-contract" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M.172 15.828a.5.5 0 0 0 .707 0l4.096-4.096V14.5a.5.5 0 1 0 1 0v-3.975a.5.5 0 0 0-.5-.5H1.5a.5.5 0 0 0 0 1h2.768L.172 15.121a.5.5 0 0 0 0 .707M15.828.172a.5.5 0 0 0-.707 0l-4.096 4.096V1.5a.5.5 0 1 0-1 0v3.975a.5.5 0 0 0 .5.5H14.5a.5.5 0 0 0 0-1h-2.768L15.828.879a.5.5 0 0 0 0-.707"/></svg>',
  undo: '<svg class="icon i20 bi bi-arrow-counterclockwise" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 3a5 5 0 1 1-4.546 2.914.5.5 0 0 0-.908-.417A6 6 0 1 0 8 2z"/><path d="M8 4.466V.534a.25.25 0 0 0-.41-.192L5.23 2.308a.25.25 0 0 0 0 .384l2.36 1.966A.25.25 0 0 0 8 4.466"/></svg>',
  mod_clear: '<svg class="icon i20 bi bi-trash3-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M11 1.5v1h3.5a.5.5 0 0 1 0 1h-.538l-.853 10.66A2 2 0 0 1 11.115 16h-6.23a2 2 0 0 1-1.994-1.84L2.038 3.5H1.5a.5.5 0 0 1 0-1H5v-1A1.5 1.5 0 0 1 6.5 0h3A1.5 1.5 0 0 1 11 1.5m-5 0v1h4v-1a.5.5 0 0 0-.5-.5h-3a.5.5 0 0 0-.5.5M4.5 5.029l.5 8.5a.5.5 0 1 0 .998-.06l-.5-8.5a.5.5 0 1 0-.998.06m6.53-.528a.5.5 0 0 0-.528.47l-.5 8.5a.5.5 0 0 0 .998.058l.5-8.5a.5.5 0 0 0-.47-.528M8 4.5a.5.5 0 0 0-.5.5v8.5a.5.5 0 0 0 1 0V5a.5.5 0 0 0-.5-.5"/></svg>',
  edit: '<svg class="icon i18 bi bi-pencil-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M12.854.146a.5.5 0 0 0-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 0 0 0-.708zm.646 6.061L9.793 2.5 3.293 9H3.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.207zm-7.468 7.468A.5.5 0 0 1 6 13.5V13h-.5a.5.5 0 0 1-.5-.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.5-.5V10h-.5a.5.5 0 0 1-.175-.032l-.179.178a.5.5 0 0 0-.11.168l-2 5a.5.5 0 0 0 .65.65l5-2a.5.5 0 0 0 .168-.11z"/></svg>',
  auto: '<svg class="icon i20 bi bi-play-fill" fill="currentColor" viewBox="0 0 16 16"><path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393"/></svg>',
  mod_archive: '<svg class="icon i20 bi bi-archive-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M12.643 15C13.979 15 15 13.845 15 12.5V5H1v7.5C1 13.845 2.021 15 3.357 15zM5.5 7h5a.5.5 0 0 1 0 1h-5a.5.5 0 0 1 0-1M.8 1a.8.8 0 0 0-.8.8V3a.8.8 0 0 0 .8.8h14.4A.8.8 0 0 0 16 3V1.8a.8.8 0 0 0-.8-.8z"/></svg>',
  people: '<svg class="icon i20 bi bi-people-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M7 14s-1 0-1-1 1-4 5-4 5 3 5 4-1 1-1 1zm4-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6m-5.784 6A2.24 2.24 0 0 1 5 13c0-1.355.68-2.75 1.936-3.72A6.3 6.3 0 0 0 5 9c-4 0-5 3-5 4s1 1 1 1zM4.5 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5"/></svg>',
  home_open: '<svg class="icon i20 bi bi-house-door-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M6.5 14.5v-3.505c0-.245.25-.495.5-.495h2c.25 0 .5.25.5.5v3.5a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 .5-.5v-7a.5.5 0 0 0-.146-.354L13 5.793V2.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5v1.293L8.354 1.146a.5.5 0 0 0-.708 0l-6 6A.5.5 0 0 0 1.5 7.5v7a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 .5-.5"/></svg>',
  home: '<svg class="icon i20 bi bi-house-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M8.707 1.5a1 1 0 0 0-1.414 0L.646 8.146a.5.5 0 0 0 .708.708L8 2.207l6.646 6.647a.5.5 0 0 0 .708-.708L13 5.793V2.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5v1.293z"/><path d="m8 3.293 6 6V13.5a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 2 13.5V9.293z"/></svg>',
  access_private: '<svg class="icon i18 bi bi-lock-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2m3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2"/></svg>',
  access_public: '<svg class="icon i18 bi bi-unlock-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M11 1a2 2 0 0 0-2 2v4a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h5V3a3 3 0 0 1 6 0v4a.5.5 0 0 1-1 0V3a2 2 0 0 0-2-2"/></svg>',
  tick: '<svg class="icon i20 bi bi-check-lg" fill="currentColor" viewBox="0 0 16 16"><path d="M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06.733.733 0 0 1 1.047 0l3.052 3.093 5.4-6.425z"/></svg>',
  edit_indent: '<svg class="icon i20 bi bi-indent" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M3 8a.5.5 0 0 1 .5-.5h6.793L8.146 5.354a.5.5 0 1 1 .708-.708l3 3a.5.5 0 0 1 0 .708l-3 3a.5.5 0 0 1-.708-.708L10.293 8.5H3.5A.5.5 0 0 1 3 8"/><path fill-rule="evenodd" d="M12.5 4a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 .5-.5"/></svg>',
  edit_dedent: '<svg class="icon i20 bi bi-unindent" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M13 8a.5.5 0 0 0-.5-.5H5.707l2.147-2.146a.5.5 0 1 0-.708-.708l-3 3a.5.5 0 0 0 0 .708l3 3a.5.5 0 0 0 .708-.708L5.707 8.5H12.5A.5.5 0 0 0 13 8"/><path fill-rule="evenodd" d="M3.5 4a.5.5 0 0 0-.5.5v7a.5.5 0 0 0 1 0v-7a.5.5 0 0 0-.5-.5"/></svg>',
  view_columns: '<svg class="icon i20 bi bi-layout-three-columns" fill="currentColor" viewBox="0 0 16 16"><path d="M0 1.5A1.5 1.5 0 0 1 1.5 0h13A1.5 1.5 0 0 1 16 1.5v13a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 0 14.5zM1.5 1a.5.5 0 0 0-.5.5v13a.5.5 0 0 0 .5.5H5V1zM10 15V1H6v14zm1 0h3.5a.5.5 0 0 0 .5-.5v-13a.5.5 0 0 0-.5-.5H11z"/></svg>',
  view_details: '<svg class="icon i20" fill="currentColor" viewBox="0 0 16 16"><ellipse cx="7.6" cy="4.3" rx="4" ry="3"/><ellipse cx="11.7" cy="4.6" rx="4" ry="3"/><ellipse cx="6.9" cy="8.5" rx="4" ry="3"/><ellipse cx="10.7" cy="7.3" rx="4" ry="3"/><ellipse cx="4.3" cy="6.3" rx="4" ry="3"/><ellipse cx="3.22" cy="12.3" rx="1.2" ry=".9"/><ellipse cx="1.4" cy="14.1" rx=".8" ry=".6"/></svg>',
  view_compact: '<svg class="icon i20 bi bi-arrows-collapse-vertical" fill="currentColor" viewBox="0 0 16 16"><path d="M8 15a.5.5 0 0 1-.5-.5v-13a.5.5 0 0 1 1 0v13a.5.5 0 0 1-.5.5M0 8a.5.5 0 0 1 .5-.5h3.793L3.146 6.354a.5.5 0 1 1 .708-.708l2 2a.5.5 0 0 1 0 .708l-2 2a.5.5 0 0 1-.708-.708L4.293 8.5H.5A.5.5 0 0 1 0 8m11.707.5 1.147 1.146a.5.5 0 0 1-.708.708l-2-2a.5.5 0 0 1 0-.708l2-2a.5.5 0 0 1 .708.708L11.707 7.5H15.5a.5.5 0 0 1 0 1z"/></svg>',
  audio: '<svg class="icon i20 bi bi-headset" fill="currentColor" viewBox="0 0 16 16"><path d="M8 1a5 5 0 0 0-5 5v1h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a6 6 0 1 1 12 0v6a2.5 2.5 0 0 1-2.5 2.5H9.366a1 1 0 0 1-.866.5h-1a1 1 0 1 1 0-2h1a1 1 0 0 1 .866.5H11.5A1.5 1.5 0 0 0 13 12h-1a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1h1V6a5 5 0 0 0-5-5"/></svg>',
  view_ids: '<svg class="icon i20 bi bi-hash" fill="currentColor" viewBox="0 0 16 16"><path d="M8.39 12.648a1 1 0 0 0-.015.18c0 .305.21.508.5.508.266 0 .492-.172.555-.477l.554-2.703h1.204c.421 0 .617-.234.617-.547 0-.312-.188-.53-.617-.53h-.985l.516-2.524h1.265c.43 0 .618-.227.618-.547 0-.313-.188-.524-.618-.524h-1.046l.476-2.304a1 1 0 0 0 .016-.164.51.51 0 0 0-.516-.516.54.54 0 0 0-.539.43l-.523 2.554H7.617l.477-2.304c.008-.04.015-.118.015-.164a.51.51 0 0 0-.523-.516.54.54 0 0 0-.531.43L6.53 5.484H5.414c-.43 0-.617.22-.617.532s.187.539.617.539h.906l-.515 2.523H4.609c-.421 0-.609.219-.609.531s.188.547.61.547h.976l-.516 2.492c-.008.04-.015.125-.015.18 0 .305.21.508.5.508.265 0 .492-.172.554-.477l.555-2.703h2.242zm-1-6.109h2.266l-.515 2.563H6.859l.532-2.563z"/></svg>',
  room_ops_copy: '<svg class="icon i20 bi bi-copy" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1zM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1z"/></svg>',
  nav_porch: '<svg class="icon i20 bi bi-house-door-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M6.5 14.5v-3.505c0-.245.25-.495.5-.495h2c.25 0 .5.25.5.5v3.5a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 .5-.5v-7a.5.5 0 0 0-.146-.354L13 5.793V2.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5v1.293L8.354 1.146a.5.5 0 0 0-.708 0l-6 6A.5.5 0 0 0 1.5 7.5v7a.5.5 0 0 0 .5.5h4a.5.5 0 0 0 .5-.5"/></svg>',
  nav_home: '<svg class="icon i20 bi bi-house-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M8.707 1.5a1 1 0 0 0-1.414 0L.646 8.146a.5.5 0 0 0 .708.708L8 2.207l6.646 6.647a.5.5 0 0 0 .708-.708L13 5.793V2.5a.5.5 0 0 0-.5-.5h-1a.5.5 0 0 0-.5.5v1.293z"/><path d="m8 3.293 6 6V13.5a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 2 13.5V9.293z"/></svg>',
  nav_allychat: '<svg class="icon i20 bi bi-people-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M7 14s-1 0-1-1 1-4 5-4 5 3 5 4-1 1-1 1zm4-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6m-5.784 6A2.24 2.24 0 0 1 5 13c0-1.355.68-2.75 1.936-3.72A6.3 6.3 0 0 0 5 9c-4 0-5 3-5 4s1 1 1 1zM4.5 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5"/></svg>',
  room_ops: '<svg class="icon i20 bi bi-file-text" fill="currentColor" viewBox="0 0 16 16"><path d="M5 4a.5.5 0 0 0 0 1h6a.5.5 0 0 0 0-1zm-.5 2.5A.5.5 0 0 1 5 6h6a.5.5 0 0 1 0 1H5a.5.5 0 0 1-.5-.5M5 8a.5.5 0 0 0 0 1h6a.5.5 0 0 0 0-1zm0 2a.5.5 0 0 0 0 1h3a.5.5 0 0 0 0-1z"/><path d="M2 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2zm10-1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1"/></svg>',
  scroll: '<svg class="icon i20 bi bi-arrows-move" fill="currentColor" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M7.646.146a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1-.708.708L8.5 1.707V5.5a.5.5 0 0 1-1 0V1.707L6.354 2.854a.5.5 0 1 1-.708-.708zM8 10a.5.5 0 0 1 .5.5v3.793l1.146-1.147a.5.5 0 0 1 .708.708l-2 2a.5.5 0 0 1-.708 0l-2-2a.5.5 0 0 1 .708-.708L7.5 14.293V10.5A.5.5 0 0 1 8 10M.146 8.354a.5.5 0 0 1 0-.708l2-2a.5.5 0 1 1 .708.708L1.707 7.5H5.5a.5.5 0 0 1 0 1H1.707l1.147 1.146a.5.5 0 0 1-.708.708zM10 8a.5.5 0 0 1 .5-.5h3.793l-1.147-1.146a.5.5 0 0 1 .708-.708l2 2a.5.5 0 0 1 0 .708l-2 2a.5.5 0 0 1-.708-.708L14.293 8.5H10.5A.5.5 0 0 1 10 8"/></svg>',
  view_advanced: '<svg class="icon i20 bi bi-lightbulb-fill" fill="currentColor" viewBox="0 0 16 16"><path d="M2 6a6 6 0 1 1 10.174 4.31c-.203.196-.359.4-.453.619l-.762 1.769A.5.5 0 0 1 10.5 13h-5a.5.5 0 0 1-.46-.302l-.761-1.77a2 2 0 0 0-.453-.618A5.98 5.98 0 0 1 2 6m3 8.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 0 1l-.224.447a1 1 0 0 1-.894.553H6.618a1 1 0 0 1-.894-.553L5.5 15a.5.5 0 0 1-.5-.5"/></svg>',
  add_math: 'Σ',  // capital sigma
  view_history: '<svg class="icon i20 bi bi-clock-history" fill="currentColor" viewBox="0 0 16 16"><path d="M8.515 1.019A7 7 0 0 0 8 1V0a8 8 0 0 1 .589.022zm2.004.45a7 7 0 0 0-.985-.299l.219-.976q.576.129 1.126.342zm1.37.71a7 7 0 0 0-.439-.27l.493-.87a8 8 0 0 1 .979.654l-.615.789a7 7 0 0 0-.418-.302zm1.834 1.79a7 7 0 0 0-.653-.796l.724-.69q.406.429.747.91zm.744 1.352a7 7 0 0 0-.214-.468l.893-.45a8 8 0 0 1 .45 1.088l-.95.313a7 7 0 0 0-.179-.483m.53 2.507a7 7 0 0 0-.1-1.025l.985-.17q.1.58.116 1.17zm-.131 1.538q.05-.254.081-.51l.993.123a8 8 0 0 1-.23 1.155l-.964-.267q.069-.247.12-.501m-.952 2.379q.276-.436.486-.908l.914.405q-.24.54-.555 1.038zm-.964 1.205q.183-.183.35-.378l.758.653a8 8 0 0 1-.401.432z"/><path d="M8 1a7 7 0 1 0 4.95 11.95l.707.707A8.001 8.001 0 1 1 8 0z"/><path d="M7.5 3a.5.5 0 0 1 .5.5v5.21l3.248 1.856a.5.5 0 0 1-.496.868l-3.5-2A.5.5 0 0 1 7 9V3.5a.5.5 0 0 1 .5-.5"/></svg>',
  font_expand: '<svg class="icon i20 bi bi-fonts" fill="currentColor" viewBox="0 0 16 16"><path d="M12.258 3h-8.51l-.083 2.46h.479c.26-1.544.758-1.783 2.693-1.845l.424-.013v7.827c0 .663-.144.82-1.3.923v.52h4.082v-.52c-1.162-.103-1.306-.26-1.306-.923V3.602l.431.013c1.934.062 2.434.301 2.693 1.846h.479z"/></svg>',
  view_fullscreen: '<svg width="20" height="20" fill="currentColor" class="bi bi-arrows-fullscreen" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M5.828 10.172a.5.5 0 0 0-.707 0l-4.096 4.096V11.5a.5.5 0 0 0-1 0v3.975a.5.5 0 0 0 .5.5H4.5a.5.5 0 0 0 0-1H1.732l4.096-4.096a.5.5 0 0 0 0-.707m4.344 0a.5.5 0 0 1 .707 0l4.096 4.096V11.5a.5.5 0 1 1 1 0v3.975a.5.5 0 0 1-.5.5H11.5a.5.5 0 0 1 0-1h2.768l-4.096-4.096a.5.5 0 0 1 0-.707m0-4.344a.5.5 0 0 0 .707 0l4.096-4.096V4.5a.5.5 0 1 0 1 0V.525a.5.5 0 0 0-.5-.5H11.5a.5.5 0 0 0 0 1h2.768l-4.096 4.096a.5.5 0 0 0 0 .707m-4.344 0a.5.5 0 0 1-.707 0L1.025 1.732V4.5a.5.5 0 0 1-1 0V.525a.5.5 0 0 1 .5-.5H4.5a.5.5 0 0 1 0 1H1.732l4.096 4.096a.5.5 0 0 1 0 .707"/></svg>',
  audio_stt: '<svg width="20" height="20" fill="currentColor" class="bi bi-mic-fill" viewBox="0 0 16 16"><path d="M5 3a3 3 0 0 1 6 0v5a3 3 0 0 1-6 0z"/><path d="M3.5 6.5A.5.5 0 0 1 4 7v1a4 4 0 0 0 8 0V7a.5.5 0 0 1 1 0v1a5 5 0 0 1-4.5 4.975V15h3a.5.5 0 0 1 0 1h-7a.5.5 0 0 1 0-1h3v-2.025A5 5 0 0 1 3 8V7a.5.5 0 0 1 .5-.5"/></svg>',
  audio_tts: '<svg width="20" height="20" fill="currentColor" class="bi bi-volume-up-fill" viewBox="0 0 16 16"><path d="M11.536 14.01A8.47 8.47 0 0 0 14.026 8a8.47 8.47 0 0 0-2.49-6.01l-.708.707A7.48 7.48 0 0 1 13.025 8c0 2.071-.84 3.946-2.197 5.303z"/><path d="M10.121 12.596A6.48 6.48 0 0 0 12.025 8a6.48 6.48 0 0 0-1.904-4.596l-.707.707A5.48 5.48 0 0 1 11.025 8a5.48 5.48 0 0 1-1.61 3.89z"/><path d="M8.707 11.182A4.5 4.5 0 0 0 10.025 8a4.5 4.5 0 0 0-1.318-3.182L8 5.525A3.5 3.5 0 0 1 9.025 8 3.5 3.5 0 0 1 8 10.475zM6.717 3.55A.5.5 0 0 1 7 4v8a.5.5 0 0 1-.812.39L3.825 10.5H1.5A.5.5 0 0 1 1 10V6a.5.5 0 0 1 .5-.5h2.325l2.363-1.89a.5.5 0 0 1 .529-.06"/></svg>',
  audio_vad: '<svg width="20" height="20" fill="currentColor" class="bi bi-soundwave" viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8.5 2a.5.5 0 0 1 .5.5v11a.5.5 0 0 1-1 0v-11a.5.5 0 0 1 .5-.5m-2 2a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 .5-.5m4 0a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 .5-.5m-6 1.5A.5.5 0 0 1 5 6v4a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m8 0a.5.5 0 0 1 .5.5v4a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m-10 1A.5.5 0 0 1 3 7v2a.5.5 0 0 1-1 0V7a.5.5 0 0 1 .5-.5m12 0a.5.5 0 0 1 .5.5v2a.5.5 0 0 1-1 0V7a.5.5 0 0 1 .5-.5"/></svg>',
};


function setup_icons() {
  for (const prefix of ["mod", "add", "view", "opt", "nav", "scroll", "room_ops", "audio"]) {
    icons[`${prefix}_cancel`] = icons["x"];
  }
  icons["edit_close"] = icons["x"];
  for (const prefix of ["rec", "rec_preview"]) {
    icons[`${prefix}_cancel`] = icons["x_large"];
  }
  for (const id of ["rec_save", "rec_preview_save", "edit_save"]) {
    icons[id] = icons["tick"];
  }
  icons["mod_undo"] = icons["x_large"];
  icons["mod_clean"] = icons["view_clean"];
  icons["mod_retry"] = icons["undo"];
  icons["edit_reset"] = icons["undo"];
  icons["edit_clear"] = icons["mod_clear"];
  icons["mod_edit"] = icons["edit"];
  icons["room_ops_move"] = icons["edit"];
  icons["access_denied"] = icons["x_large"];
  icons["add_file_2"] = icons["add_file"];
  icons["font_contract"] = icons["font_expand"];
  icons["mod_auto"] = icons["auto"];
  icons["audio_auto"] = icons["auto"];

  for (const id in icons) {
    const el = $id(id);
    if (!el)
      continue;
    const text = el.textContent;
    el.title = el.title || text;
    el.innerHTML = icons[id];
  }
}

// math input ----------------------------------------------------------------

async function add_math_input(ev) {
  if (ev.inputType === "insertLineBreak")
    await add_math(ev);
}

async function add_math(ev) {
  if (ev) {
    ev.preventDefault();
    ev.stopPropagation();
  }
  await $script("script_mathlive", "https://unpkg.com/mathlive");
  MathfieldElement.soundsDirectory = null;
  MathfieldElement.keypressVibration = null;
  // hide normal input, show the <math-field> container
  if (active_toggle("add_math")) {
    console.log("add_math");
    // if any text in selected in content, put it in the math input
    // TODO perhaps expand from caret to the surrounding math delimiters :/
    let selected_text = $content.value.substring($content.selectionStart, $content.selectionEnd);
    // strip $ from both ends
    selected_text = selected_text.replace(/^\$|\$$/g, "");
    $math_input.value = selected_text;
    hide($content);
    show($math_input);
    $math_input.focus();
  } else {
    console.log("add_math cancel");
    hide($math_input);
    show($content);
    $content.focus();

    // insert $id("math-input").value into the content field at the cursor
    let tex_math = $math_input.value.trim();
    if (tex_math)
      tex_math = "$" + tex_math + "$";
    $math_input.value = "";
    setRangeText($content, tex_math, $content.selectionStart, $content.selectionEnd);
  }
}

// printing ------------------------------------------------------------------

function print_chat(ev) {
  ev.preventDefault();  /* doesn't! WTF */
  // TODO: view options! could save them in local storage in the room, maybe?
  const url = room_url() + "?snapshot=1#print";
  window.location.href = url;
}

// main ----------------------------------------------------------------------

export async function init() {
  user = await authChat();

  setup_icons();
  load_theme();
  setup_dev();
  set_debug(DEBUG);
  on_hash_change();

  $on($id("send"), "click", send);

  $on($id("add"), "click", () => set_controls("input_add"));
  $on($id("mod"), "click", () => set_controls("input_mod"));
  $on($id("view"), "click", () => set_controls("input_view"));
  $on($id("opt"), "click", () => set_controls("input_opt"));
  $on($id("audio"), "click", () => set_controls("input_audio"));

  $on($id("nav"), "click", () => set_top_left("top_left_nav"));
  $on($id("scroll"), "click", () => set_top("top_scroll"));
  $on($id("room_ops"), "click", () => set_top_left("top_left_room_ops"));

  $on($id("mod_undo"), "click", undo);
  $on($id("mod_retry"), "click", retry);
  $on($id("mod_clear"), "click", clear_chat);
  $on($id("mod_archive"), "click", archive_chat);
  $on($id("mod_clean"), "click", clean_chat);
  // $on($id('mod_rotate'), 'click', rotate_chat);
  $on($id("mod_auto"), "click", auto_play);
  $on($id("mod_edit"), "click", () => edit());
  $on($id("mod_cancel"), "click", () => set_controls());

  $on($id("add_file"), "click", file_clicked);
  $on($id("add_file_2"), "click", file_clicked);
  $on($id("add_math"), "click", add_math);
  $on($math_input, "input", add_math_input);
  $on($id("files"), "change", files_changed);
  $on($id("add_cancel"), "click", () => set_controls());

  $on($id("edit_save"), "click", edit_save_and_close);
  $on($id("edit_reset"), "click", edit_reset);
  $on($id("edit_clear"), "click", edit_clear);
  $on($id("edit_close"), "click", edit_close);
  $on($id("edit_indent"), "click", edit_indent);
  $on($id("edit_dedent"), "click", edit_dedent);

  $on($id("view_theme"), "click", change_theme);
  $on($id("view_ids"), "click", view_ids);
  $on($id("view_images"), "click", view_images);
  $on($id("view_alt"), "click", view_alt);
  $on($id("view_image_size"), "click", view_image_size);
  $on($id("view_font_size"), "click", view_font_size);
  $on($id("view_source"), "click", view_source);
  $on($id("view_highlight"), "click", view_highlight);
  $on($id("view_details"), "click", view_details);
  $on($id("view_canvas"), "click", view_canvas);
  $on($id("view_clean"), "click", view_clean);
  $on($id("view_columns"), "click", view_columns);
  $on($id("view_compact"), "click", view_compact);
  $on($id("view_history"), "click", view_history);
  $on($id("view_fullscreen"), "click", view_fullscreen);
  $on($id("view_items"), "change", view_items);
  $on($id("view_items"), "keyup", view_items);
  $on($id("view_advanced"), "click", view_advanced);
  $on($id("view_cancel"), "click", () => set_controls());

  $on($id("opt_context"), "change", opt_context);
  $on($id("opt_lines"), "change", opt_lines);
  $on($id("opt_images"), "change", opt_images);
  $on($id("opt_mission"), "change", opt_mission);
  $on($id("opt_cancel"), "click", () => set_controls());

  $on($id("nav_cancel"), "click", () => set_top_left());

  $on($id("scroll_home"), "click", (ev) => scroll_home_end(ev, 0));
  $on($id("scroll_end"), "click", (ev) => scroll_home_end(ev, 1));
  $on($id("scroll_pageup"), "click", (ev) => scroll_pages(ev, -1));
  $on($id("scroll_pagedown"), "click", (ev) => scroll_pages(ev, 1));
  $on($id("scroll_cancel"), "click", () => set_top());

  $on($id("room_ops_move"), "click", move_mode);
  $on($id("room_ops_copy"), "click", copy_mode);
  $on($id("room_ops_cancel"), "click", () => set_top_left());

  $on($id("audio_cancel"), "click", () => set_controls());

  $on(document, "keydown", (ev) => dispatch_shortcut(ev, shortcuts.global));
  $on($content, "keydown", (ev) => dispatch_shortcut(ev, shortcuts.message));
  $on($content, "keydown", content_keydown);
  $on($room, "keypress", (ev) => dispatch_shortcut(ev, shortcuts.room));
  $on($edit, "keydown", (ev) => dispatch_shortcut(ev, shortcuts.edit));
  $on($content, "input", message_changed);

  $on($room, "change", () => set_room());
  $on(window, "hashchange", on_hash_change);
  $on(window, "message", handle_message);
  const dragControls = initDragControls();
  $on($id("resizer"), "mousedown", dragControls);
  $on($id("resizer"), "touchstart", dragControls);

  $on(window, "beforeprint", print_chat);

  $on(document, "fullscreenchange", fullscreenchange);

  $content.addEventListener('dragover', content_dragover);
  $content.addEventListener('dragleave', content_dragleave);
  $content.addEventListener('drop', content_drop);
  $content.addEventListener('paste', content_paste);

  setup_view_options();

  notify_main();
  record_main();

  message_changed();
  // $content.focus();

  await load_user_styles_and_script();

  /* This breaks scrolling in view_edit, etc, and I forget why I added it!
  $on(document, "touchmove", function(e) {
    e.preventDefault();
  }, { passive: false });
  */
}
