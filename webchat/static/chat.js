const ROOMS_URL =
  location.protocol + "//" + location.host.replace(/^chat\b/, "rooms");
const MAX_ROOM_NUMBER = 1e3; // 1e12;
const DEFAULT_ROOM = "Ally Chat";

// TODO: no!
const global_moderators = ["root", "sam"];
const devs = ["root", "sam"];

const $head = $("head");
const $room = $id("room");
const $content = $id("content");
const $messages_iframe = $id("messages_iframe");
const $form = $id("form");
const $title = $("title");
const $inputrow = $id("inputrow");
const $edit = $id("view_edit");
const $auto = $id('mod_auto');
const $messages_overlay = $id("messages_overlay");

const narrator = "Nova";
const illustrator = "Pixi";


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
let view = "messages";

let room_ready = false;
let theme;

const ADMIN = "admin";

// keyboard shortcuts --------------------------------------------------------

const SHORTCUTS_GLOBAL = shortcuts_to_dict([
  ['escape', escape, 'Go back, change or leave room'],
  ['ctrl+;', change_room, 'Change room'],
  ["ctrl+'", room_clear_number, "Clear room number"],
  ['ctrl+.', room_next, 'Go to next room'],
  ['ctrl+,', room_prev, 'Go to previous room'],
  ['ctrl+/', room_random, 'Go to random room'],
]);

const SHORTCUTS_MESSAGE = shortcuts_to_dict([
  ['ctrl+enter', () => send(), 'Send message'],
  ['shift+enter', send_random_message, 'Send a random message'],
  ['alt+enter', poke, 'Poke the chat'],
  ['alt+s', send, 'Send message'],
  ['alt+p', poke, 'Poke the chat'],
  ['alt+t', content_insert_tab, 'Insert tab'],
  ['shift+alt+t', content_insert_tab, 'Insert tab'],
  ['alt+backspace', clear_content, 'Clear content'],
  ['alt+u', browse_up, 'Browse up'],
  ['alt+i', view_images, 'View images'],
  ['alt+c', view_clean, 'View clean'],

  ['alt+z', undo, 'Undo last action', ADMIN],
  ['alt+r', retry, 'Retry last action', ADMIN],
  ['alt+x', clear_chat, 'Clear messages', ADMIN],
  ['alt+a', archive_chat, 'Archive chat', ADMIN],
  ['shift+alt+c', clean_chat, 'Clean up the room', ADMIN],
  ['alt+e', () => edit(), 'Edit file', ADMIN],

  ['alt+n', () => invoke(narrator), 'Invoke the narrator'],
  ['alt+v', () => invoke(illustrator), 'Invoke the illustrator'],
  ['alt+/', () => invoke("anyone"), 'Invoke anyone randomly'],
  ['shift+alt+/', () => invoke("everyone"), 'Invoke everyone'],
]);

const SHORTCUTS_ROOM = shortcuts_to_dict([
  ['enter', focus_content, 'Focus message input'],
]);

const SHORTCUTS_EDIT = shortcuts_to_dict([
  ['alt+t', edit_insert_tab, 'Insert tab'],
  ['shift+alt+t', edit_insert_tab, 'Insert tab'],
  ['escape', edit_close, 'Close edit'],
  ['ctrl+s', edit_save, 'Save edit'],
  ['ctrl+enter', edit_save_and_close, 'Save edit and close'],
  ['alt+z', edit_reset, 'Reset edit'],
  ['alt+x', edit_clear, 'Clear edit'],
]);

// developer functions -------------------------------------------------------

const real_console_log = console.log;

function set_debug(debug) {
  DEBUG = debug;
  console.log = DEBUG ? real_console_log : () => {};
  active_set("debug", DEBUG);
}

function setup_dev() {
  dev = devs.includes(user);
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
  $content.focus();
}

function send_random_message() {
  const message = random_message[Math.floor(Math.random() * random_message.length)];
  send_text(message);
}

// error indicator for buttons -----------------------------------------------

async function flash($el, className) {
  $el.classList.add(className);
  await $wait(300);
  $el.classList.remove(className);
}

async function error(id) {
  await flash($id(id), "error");
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
  if (count > 0)
    $el.classList.remove(`active-${Math.min(count, active_max_class)}`);
  count = active_counts[id] = Math.max(new_count, 0);
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
  }
}

// insert tabs and indent ----------------------------------------------------

function textarea_indent(textarea, dedent = false) {
  // If no selection, handle single tab insertion/removal
  if (textarea.selectionStart === textarea.selectionEnd) {
    if (dedent) {
      // For shift-tab with no selection, remove previous tab if it exists
      const pos = textarea.selectionStart;
      if (pos > 0 && textarea.value[pos - 1] === '\t') {
        setRangeText(textarea, '', pos - 1, pos);
        textarea.selectionStart = textarea.selectionEnd = pos - 1;
      } else {
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

  // Split the selected block into lines
  const selectedText = text.slice(blockStart, blockEnd);
  const lines = selectedText.split('\n');

  // Process each line
  const processedLines = lines.map(line => {
    if (dedent) {
      // Remove one tab if it exists at the start
      return line.startsWith('\t') ? line.slice(1) : line;
    } else {
      // Add a tab
      return '\t' + line;
    }
  });

  // Join the lines back together
  const newText = processedLines.join('\n');

  // Calculate new selection positions
  const deltaPerLine = dedent ? -1 : 1;
  const newSelStart = selStart + (selStart > blockStart ? deltaPerLine : 0);
  const newSelEnd = selEnd + deltaPerLine * lines.length - (selEnd === blockEnd ? deltaPerLine : 0);

  setRangeText(textarea, newText, blockStart, blockEnd);

  // Restore selection
  textarea.setSelectionRange(newSelStart, newSelEnd);
}

function setRangeText(textarea, newText, blockStart, blockEnd) {
  // Store original selection
  const selStart = textarea.selectionStart;
  const selEnd = textarea.selectionEnd;

  // Make the replacement
  textarea.setSelectionRange(blockStart, blockEnd);
  document.execCommand('insertText', false, newText);

  // Calculate how the replacement affected positions
  const lengthDiff = newText.length - (blockEnd - blockStart);

  // Restore selection, adjusting for text length changes
  const adjustedStart = selStart < blockStart ? selStart :
            selStart > blockEnd ? selStart + lengthDiff :
            blockStart;

  const adjustedEnd = selEnd < blockStart ? selEnd :
            selEnd > blockEnd ? selEnd + lengthDiff :
            blockEnd;

  textarea.setSelectionRange(adjustedStart, adjustedEnd);
}

// handle message change -----------------------------------------------------

function message_changed(ev) {
  if ($content.value == "") $id("send").textContent = "poke";
  else $id("send").textContent = "send";
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

function set_room(r) {
  // check if r was passed
  if (r === undefined) {
    r = $room.value;
  }

  const type = get_file_type(r);

  if (view === "view_edit" && type == "dir" && !edit_close()) {
    // reject changing to a directory if we have unsaved changes in the editor
    $room.value = room;
    error("room");
    return;
  }

  $room.value = r;

  clear_messages_box();
  room = r;
  set_title_hash(room);
  if (!room) return;

  //	who();

  if (type == "room" || type == "dir") {
    let stream_url = ROOMS_URL + "/" + room;
    if (type == "room") {
      stream_url += ".html";
    }
    stream_url += "?stream=1";
    messages_iframe_set_src(stream_url);
  }

  setup_user_button();
  setup_admin();

  if (view === "view_edit") {
    editor_file = r;
    if (type == "room")
      editor_file += ".bb";
    editor_text_orig = null;
  } else if (type == "file") {
    // start editing the file
    edit(r);
  }

  if (view !== "view_edit")
    reset_ui();
}

function browse_up(ev) {
  let new_room;
  if (room.match(/\/$/)) {
    new_room = room.replace(/\/$/, "");
  } else {
    new_room = room.replace(/[^\/]+$/, "") || "/";
  }
  set_room(new_room);
}

// user info and settings ----------------------------------------------------

function load_theme() {
  let $link = $id("user_styles");
  if (!$link) {
    $link = $create("link");
    $link.id = "user_styles";
    $link.rel = "stylesheet";
    $link.type = "text/css";
    $head.append($link);
  }
  if (theme) {
    $link.href = "/themes/" + theme + ".css";
  } else {
    $link.href = "/users/" + user + "/theme.css";
  }
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

function set_title_hash(query) {
  new_hash = query_to_hash(query);
  new_title = query_to_title(query);
  if (location.hash != new_hash)
    location.hash = new_hash;
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

function leave_room() {
  // the following doesn't work reliably, so we're going out out
  if (room == "-") set_room("");
  else set_room("-");
}

function change_room() {
  if ($room === document.activeElement) {
    leave_room();
  } else {
    $room.focus();
    $room.select();
  }
  return false;
}

function escape() {
  if (controls !== "input_main") {
    set_controls();
    set_view();
  } else {
    change_room();
  }
}

// room numbers --------------------------------------------------------------

function room_set_number(n) {
  if (n === "") {
    room = room.replace(/-?\d+$/, "");
    set_room(room);
    return;
  }
  if (n < 0) {
    n = 0;
  }
  if (n > MAX_ROOM_NUMBER) {
    n = MAX_ROOM_NUMBER;
  }
  room = room.replace(/-?\d+$|$/, "-" + n);
  set_room(room);
}

function room_get_number() {
  const match = room.match(/(\d+)$/);
  return match ? match[1] : null;
}

function room_random() {
  room_set_number(Math.floor(Math.random() * (MAX_ROOM_NUMBER + 1)));
}

function room_next() {
  let num = room_get_number();
  if (num === null) {
    num = 0;
  } else {
    num = +num + 1;
  }
  room_set_number(num);
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
  room_set_number(num);
}

function room_clear_number() {
  room_set_number("");
}

// Keyboard shortcuts handling -----------------------------------------------

function content_insert_tab(ev) {
  textarea_indent($content, ev.shiftKey);
}

function edit_insert_tab(ev) {
  textarea_indent($edit, ev.shiftKey);
}

function shortcuts_to_dict(shortcuts) {
  const dict = {};
  for (const [key, fn, desc, admin] of shortcuts) {
    dict[key] = { fn, desc, admin };
  }
  return dict;
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

// reload the page -----------------------------------------------------------

let reloading = false;

function reload_page() {
  if (reloading) return;
  reloading = true;
  location.reload();
}

// handle messages from the messages iframe ----------------------------------

function handle_message(ev) {
  if (ev.origin != ROOMS_URL) {
    console.error("ignoring message from", ev.origin);
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
  }

  if (ev.data.type == "overlay") {
    set_overlay(ev.data.overlay);
    return;
  }

  $content.focus();

  // detect F5 or ctrl-R to reload the page
  if (
    ev.data.type == "keydown" &&
    (ev.data.key == "F5" ||
      (ev.data.ctrlKey && ev.data.key.toLowerCase() == "r"))
  ) {
    reload_page();
    return;
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

// Register service worker ---------------------------------------------------

let sw_registration;
let sw_message_channel;

function handle_sw_message(event) {
  if (event.data.type == "APP_INFO") {
    VERSION = event.data.version;
    $id("debug").textContent = VERSION;
  }
}

function sw_updatefound() {
  const newWorker = sw_registration.installing;

  // Listen for state changes on the new service worker
  newWorker.addEventListener("statechange", sw_statechange);
}

function sw_statechange(ev) {
  if (ev.target.state === "activated") reload_page();
}

async function register_service_worker() {
  if (!"serviceWorker" in navigator) return;
  try {
    sw_registration = await navigator.serviceWorker.register(
      "/service_worker.js"
    );
    // console.log("ServiceWorker registration successful");
  } catch (err) {
    console.error("ServiceWorker registration failed: ", err);
    return;
  }

  await navigator.serviceWorker.ready;

  sw_registration.addEventListener("updatefound", sw_updatefound);
  sw_registration.update();

  // Request the app version from the service worker
  sw_message_channel = new MessageChannel();
  sw_registration.active.postMessage({ type: "PORT_INITIALIZATION" }, [
    sw_message_channel.port2,
  ]);
  sw_message_channel.port1.onmessage = handle_sw_message;
  sw_message_channel.port1.postMessage("getAppInfo");
}

// authentication ------------------------------------------------------------

function authChat() {
  $on($id("logout"), "click", logoutChat);
  userData = getJSONCookie("user_data");
  if (!userData) throw new Error("Setup error: Not logged in");

  return userData.username;
}

// set the user button text and href -----------------------------------------

function setup_user_button() {
  const $user = $id("user");
  $user.innerText = user;
  if (room == user) $user.href = "/" + query_to_hash(DEFAULT_ROOM);
  else $user.href = "/" + query_to_hash(user);
}

// Wrapper function to initialize drag controls for the input row ------------

function initDragControls() {
  const resizer = new DragResizer({
    element: $inputrow,
    direction: 'up',
    overlay: $messages_overlay,
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
  admin = global_moderators.includes(user) || top_dir == user;
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
    confirm_message = "Save and clear the chat?";
  else if (op == "clean")
    confirm_message = "Clean up the room?  Removes messages from specialists.";
  // TODO it would be better to hide them from everyone, with a switch
  else
    throw new Error("invalid op: " + op);

  if (!confirm(confirm_message)) return;

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

  // TODO should clear immediately for other users too, not just the current user
  // reload_messages();
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

async function undo(ev) {
  ev.preventDefault();

  auto_play_back_off();

  try {
    await undo_last_message(room);
    // TODO should clear immediately for other users too, not just the current user
    // reload_messages();
  } catch (err) {
    console.error(err.message);
    await error("mod_undo");
  }
}

async function retry(ev) {
  try {
    await undo(ev);
    await $wait(100);
    await poke();
  } catch (err) {
    console.error(err.message);
    await error("retry");
  }
}

// input controls ------------------------------------------------------------

let view_theme_original_text;

function set_controls(id) {
  id = id || "input_main";
  const $el = $id(id);
  if ($el.classList.contains("hidden")) {
    hide($("#inputrow > .controls:not(.hidden)"));
    show($id(id || "input_main"));
  }
  if (id === "input_main") {
    setTimeout(() => $content.focus(), 1);
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

function reset_ui() {
  set_controls();
  set_view();
  active_reset("send");
  active_reset("add_file");
  active_reset("edit_save");
  stop_auto_play();
  // TODO stop any current recording
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
  $auto.textContent = "auto";
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

EDITABLE_EXTENSIONS = [
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

DISALLOWED_EXTENSIONS = [
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
    console.log("checking mime type for file:", file);
    const mime = await check_mime_type(file);
    if (!mime.startsWith("text/")) {
      throw new Error("disallowed mime type for file: " + file + " (" + mime + ")");
    }
  }
}

async function fetch_file(file) {
  const response = await fetch(`${ROOMS_URL}/${file}?nocache=${Math.random()}`, {
    credentials: 'include'
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
    file = room + ".bb";
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
  // if it's a .bb file, and not empty, ensure it ends with a double newline
  if (!editor_file) {
    error("edit_save");
    return false;
  }

  edit_get_text();

  if (editor_file.match(/\.bb$/) && editor_text && !editor_text.match(/[^\n]\n\n$/)) {
    edit_set_text(editor_text.replace(/\n*$/, "\n\n"));
  }

  if (editor_text === editor_text_orig) {
    error("edit_save");
    return false;
  }

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

function edit_close() {
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


let view_options = {
  images: 2,
  source: 1,
};

function setup_view_options() {
  // persist from local storage JSON
  // if not present, set to default
  let view_options_str = localStorage.getItem("view_options");
  if (view_options_str) {
    view_options = JSON.parse(view_options_str);
  }
  add_hook("room_ready", view_options_apply);
}

function view_options_apply() {
  // save to local storage
  localStorage.setItem("view_options", JSON.stringify(view_options));
  // update buttons
  active_set("view_images", view_options.images || 0);
  active_set("view_source", view_options.source || 0);
  active_set("view_canvas", view_options.canvas || 0);
  active_set("view_clean", view_options.clean || 0);
  // send message to the rooms iframe to apply view options
  $messages_iframe.contentWindow.postMessage({ type: "set_view_options", ...view_options }, ROOMS_URL);
}

function view_images() {
  // goes 2, 1, 0, 2 ...
  view_options.images = (+view_options.images - 1 + 3) % 3;
  view_options_apply();
}

function view_source() {
  view_options.source = !view_options.source;
  view_options_apply();
}

function view_canvas() {
  view_options.canvas = !view_options.canvas;
  view_options_apply();
}

function view_clean() {
  view_options.clean = !view_options.clean;
  view_options_apply();
}

// invoke someone ------------------------------------------------------------

function invoke(who) {
  send_text(`-@${who}`);
}

// themes --------------------------------------------------------------------

async function fetch_themes_options() {
  const response = await fetch("/themes");
  if (!response.ok) {
    throw new Error("GET themes request failed");
  }
  const data = await response.text();
  const parser = new DOMParser();
  const doc = parser.parseFromString(data, 'text/html');
  const links = [...doc.getElementsByTagName('a')];
  links.shift();
  const hrefs = links.map(link => link.getAttribute('href'));
  const themes = hrefs.map(href => href.replace(/\.css$/, ''));
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

function show_theme() {
  $id("view_theme").textContent = theme;
}

// main ----------------------------------------------------------------------

function chat_main() {
  user = authChat();
  load_theme();
  setup_dev();
  set_debug(DEBUG);
  on_hash_change();

  $on($id("send"), "click", send);
  $on($id("up"), "click", browse_up);

  $on($id("add"), "click", () => set_controls("input_add"));
  $on($id("mod"), "click", () => set_controls("input_mod"));
  $on($id("view"), "click", () => set_controls("input_view"));

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
  $on($id("files"), "change", files_changed);
  $on($id("add_cancel"), "click", () => set_controls());

  $on($id("edit_save"), "click", edit_save);
  $on($id("edit_reset"), "click", edit_reset);
  $on($id("edit_clear"), "click", edit_clear);
  $on($id("edit_close"), "click", edit_close);

  $on($id("view_theme"), "click", change_theme);
  $on($id("view_images"), "click", view_images);
  $on($id("view_source"), "click", view_source);
  $on($id("view_canvas"), "click", view_canvas);
  $on($id("view_clean"), "click", view_clean);
  $on($id("view_cancel"), "click", () => set_controls());

  $on(document, "keydown", (ev) => dispatch_shortcut(ev, SHORTCUTS_GLOBAL));
  $on($content, "keydown", (ev) => dispatch_shortcut(ev, SHORTCUTS_MESSAGE));
  $on($content, "keydown", content_keydown);
  $on($room, "keypress", (ev) => dispatch_shortcut(ev, SHORTCUTS_ROOM));
  $on($edit, "keydown", (ev) => dispatch_shortcut(ev, SHORTCUTS_EDIT));
  $on($content, "input", message_changed);

  $on($room, "change", () => set_room());
  $on(window, "hashchange", on_hash_change);
  $on(window, "message", handle_message);
  const dragControls = initDragControls();
  $on($id("resizer"), "mousedown", dragControls);
  $on($id("resizer"), "touchstart", dragControls);

  setup_view_options();

  register_service_worker();
  notify_main();
  record_main();

  message_changed();
  $content.focus();
}
