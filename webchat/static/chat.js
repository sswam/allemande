const embed = window.parent !== window.self;

const ROOMS_URL =
  location.protocol + "//" + location.host.replace(/^chat\b/, "rooms");
const SITE_URL =
  location.protocol + "//" + location.host.replace(/^.*?\./, "") + "/";
const MAX_ROOM_NUMBER = 9999;
const EXTENSION = ".bb";
const CONFIRM_ARCHIVE = false;
let DEFAULT_ROOM = PUBLIC_ROOM;
const hold_alt = false;

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

let nsfw = false;
let is_private = false;
let is_nsfw = false;
let access_denied = false;
let icons;

const narrator = "Nova";
const illustrator = "Illu";

const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
// const isFirefox = navigator.userAgent.includes('Firefox');
// const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
const iOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
const isMac = /Macintosh|MacIntel|MacPPC|Mac68K|MacOS/i.test(navigator.userAgent);
const Alt = isMac ? "Option" : "Alt";

async function detectIncognito() {
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    const {quota} = await navigator.storage.estimate();
    return quota < 120000000;
  }
  return false;
}
const incognito = await detectIncognito();

function confirm_except_iOS(message) {
  if (iOS) return true;
  return confirm(message);
}

let lastMessageId = null;

let help_room, qa_room, help_url, qa_url;

const image_size_default = 6;
const font_size_default = 4;
let simple = true;

const VIEW_OPTIONS_DEFAULT = {
  beta_test: "simple2",
  ids: 0,
  images: 1,
  alt: 0,
  source: 0,
  details: 0,
  canvas: 0,
  toc: 1,
  clean: 0,
  columns: 0,
  compact: 0,
  history: 0,
  image_size: image_size_default,
  font_size: font_size_default,
  input_row_height: 72, // 48 // 32 // 72
  theme: "light",
  details_changed: true,
  highlight: 1,
  highlight_theme_light: "a11y-light",
  highlight_theme_dark: "a11y-dark",
  fullscreen: 0,
  advanced: -1,
  audio_stt: 0,
  audio_tts: 0,
  audio_vad: 0,
  audio_auto: 0,
  audio_voice: "ballad",
  help: 0,
  embed: 0,
  dir_sort: "time",
  filter: "",
};

let view_options = {};
function view_options_reset() {
  const preserve = {};
  const preserve_settings = ["theme", "source", "font_size", "image_size", "images", "highlight", "history", "dir_sort", "filter", "toc", "alt", "ids"];
  for (const key of preserve_settings) {
    if (view_options[key] !== undefined)
      preserve[key] = view_options[key];
  }
  view_options = { ...VIEW_OPTIONS_DEFAULT, ...preserve };
}
view_options_reset();

let mode_options = {
  select: 0,
};

let view_options_embed = {
  alt: 0,
  source: 1,
  details: 0,
  canvas: 0,
  toc: 1,
  clean: 0,
  columns: 0,
  compact: 0,
  history: 0,
  image_size: 10,
  input_row_height: 60,
  details_changed: true,
  fullscreen: 0,
  help: 0,
  embed: 1,
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

// beautiful fonts -----------------------------------------------------------

const beautiful_fonts = [
	['Playfair Display', 'serif', [400], 'https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap'],
	['Quicksand', 'sans-serif', [300, 500], 'https://fonts.googleapis.com/css2?family=Quicksand:wght@300;500&display=swap'],
	['Dancing Script', 'cursive', [400], 'https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap'],
	['Cormorant Garamond', 'serif', [300], 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;600&display=swap'],
	['Raleway', 'sans-serif', [200, 400], 'https://fonts.googleapis.com/css2?family=Raleway:wght@200;400&display=swap'],
	['Great Vibes', 'cursive', [400], 'https://fonts.googleapis.com/css2?family=Great+Vibes&display=swap'],
	['Montserrat', 'sans-serif', [300], 'https://fonts.googleapis.com/css2?family=Montserrat:wght@300&display=swap'],
	['Josefin Sans', 'sans-serif', [300, 400], 'https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@300;400&display=swap'],
];

async function load_beautiful_font() {
  const [name, family, weights, font_url] = fort(beautiful_fonts);
  const weight = fort(weights);
  await $style('beautiful-font', font_url);
  return `font-family: '${name}', ${family}; font-weight: ${weight};`
}

// background image ----------------------------------------------------------

const simple_welcome_show_background = true;

function load_background_image(i) {

}

const simple_welcome_1 = [
  "Welcome, $user. How can I help you today?",
  "Hey! What's on your mind?",
  "Good to see you, $user. Where shall we begin?",
  "Hi there, $user. I'm ready when you are.",
  "Welcome. What would you like to explore?",
];

const simple_welcome_2 = [
  "A blank canvas awaits. What shall we create?",
  "Every story needs a first line, $user. What's ours?",
  "Is there a thought you'd like to untangle today?",
  "Shall we follow a thread of curiosity, $user?",
  "What if we built something new?",
  "Have an idea looking for a spark, $user?",
  "Let's chart a new course. Where are we headed?",
  "What problem could we look at from a different angle, $user?",
  "Is there a world you'd like to imagine with me?",
  "The stage is set. What's the scene?",
];

const simple_welcome_3 = [
  "Feeling lyrical? We could write a poem or a song.",
  "Shall we sketch out a scene with words and see what comes to life, $user?",
  "Have a number to crunch or an equation to solve?",
  "How about a bit of humor? We could trade jokes or write a short comedy sketch.",
  "Shall we map out an idea or visualize some data, $user?",
  "Thinking about a new character? We can invent their story together.",
  "Want to untangle some logic, $user? We could work through some code.",
  "Curious what's happening in the world? We can discuss the latest events.",
  "Have a big idea, $user? Let's brainstorm some possibilities.",
  "Ready for an adventure? We could begin a roleplaying story.",
];

let welcome_message;

async function welcome() {
  // count how many visits in local storage
  // shuffle based on same seed each time, to avoid repetition
  let visit = +localStorage.getItem("visits");
  let seed = localStorage.getItem("seed") ?? (Math.random() * 2147483647) % 2147483647;
  localStorage.setItem("seed", seed);
  localStorage.setItem("visits", visit + 1);
  if (!simple)
    return;
  const rand = srand(seed);
  const m1 = shuf([...simple_welcome_1], rand)[visit % simple_welcome_1.length];
  const m2 = shuf([...simple_welcome_2], rand)[visit % simple_welcome_2.length];
  const m3 = shuf([...simple_welcome_3], rand)[visit % simple_welcome_3.length];

  for (let i = 0; i < visit; i++)
    rand();
  
  welcome_message = m1;
  if (incognito || visit >= 5)
    if (rand() < 0.5)
      welcome_message = m2;
  if (incognito || visit >= 15)
    if (rand() < 0.5)
      welcome_message = m3;

  const name = user.replace(/\b./g, c => c.toUpperCase());
  welcome_message = welcome_message.replace(/\$user/g, name);

  const css_text = await load_beautiful_font();
  // console.log("font css:", css_text);
  const $welcome = $id("welcome");
  $welcome.style.cssText = css_text;
  // console.log("welcome:", $welcome);

  $welcome.classList.add("invisible");
  $welcome.innerText = welcome_message;
  await $wait(500);
  $welcome.classList.remove("invisible");

  // console.log("welcome:", $welcome);

  // we send the welcome message as narrative with first message, if room is simple.empty
}


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
];

let VERSION;
export let DEBUG = true;

export let room;
let user;
let admin = false;
let dev = false;
let early = false;
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

function setup_dev_early() {
  dev = DEVS.includes(user);
  early = EARLY.includes(user);
  if (dev)
    $body.classList.add("dev");
  else
    DEBUG = false;
  if (early)
    $body.classList.add("early");
  set_debug(DEBUG);
  $on($id("debug"), "click", () => set_debug(!DEBUG));
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

  if (get_file_type($room.value) === "dir") {
    flash($id("send"), "error");
    return;
  }

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

function focus_content_on_pc() {
  // show a backtrace of this function being called
  const err = new Error();
  const stack = err.stack.split("\n").slice(1).map(line => line.trim());
  console.log("focus_content_on_pc", stack);

  if (!isMobile)
    focus_content();
}

function focus_content() {
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
  const message = "-@" + last_users[last_users.length - n];
  await send_text(message);
}


// error indicator for buttons -----------------------------------------------

async function flash($el, className) {
  $el.classList.add(className);
  await $wait(300);
  $el.classList.remove(className);
}

export async function error(id) {
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

export function active_set(id, new_count) {
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

export function active_reset(id) {
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
  if (message_user_lc != user) {
    active_dec("send");
    if (message.user) {
      // This doesn't quite work right, perhaps we don't receive the messages in order?
      // remove any existing entry
      last_users = last_users.filter(u => u != message.user);
      last_users.push(message.user);
      if (last_users.length > 10)
        last_users.shift();
    }
  }
  // FIXME some issue where it's null sometimes...
  lastMessageId = message.lastMessageId || lastMessageId;
  // console.log("new_chat_message", lastMessageId);
  // $body.classList.toggle("empty", lastMessageId === null);
  $body.classList.remove("empty");
}

// insert text ---------------------------------------------------------------

function content_insert(ev, text) {
  textarea_insert($content, text);
}

function textarea_insert(textarea, text) {
  textarea.focus();
  document.execCommand('insertText', false, text);
  message_changed();
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
  const ind = textarea == $edit && editor_file.endsWith(".yml") ? "  " : "\t";
  const indlen = ind.length;
  // If no selection, handle single tab insertion/removal
  textarea.focus();
  if (textarea.selectionStart === textarea.selectionEnd) {
    if (dedent) {
      // For shift-tab with no selection, remove previous tab if it exists  // FIXME not ideal
      const pos = textarea.selectionStart;
      if (pos >= indlen && textarea.value.slice(pos - indlen, pos) === ind) {
        setRangeText(textarea, '', pos - indlen, pos);
        textarea.selectionStart = textarea.selectionEnd = pos - indlen;
      }
    } else {
      // For tab with no selection, insert a tab at caret
      setRangeText(textarea, ind, textarea.selectionStart, textarea.selectionEnd);
      const newPos = textarea.selectionStart;
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
      if (line.startsWith(ind)) {
        processedLines.push(line.slice(indlen));
      } else if (line.startsWith('\t')) {
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
      processedLines.push(ind + line);
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

function rem_to_px(rem) {
  return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

function on_room_ready(fn, ...args) {
  if (room_ready)
    fn(...args);
  else
    add_hook("room_ready", () => fn(...args));
}

function message_changed(ev) {
  const $send = $id("send");
  if ($content.value == "" && !simple) {
    $send.innerHTML = icons["poke"];
    $send.title = `poke the chat: ${Alt}+enter`;
  } else {
    $send.innerHTML = icons["send"];
    $send.title = "send your message" + (simple ? "" : ": ctrl+enter");
  }
  if (simple) {
    const old_flexBasis = $inputrow.style.flexBasis;
    $inputrow.style.flexBasis = "0";
    // read the var(--pad) * 2
    const pad = getComputedStyle(document.body).getPropertyValue("--pad");
    const pad_px = rem_to_px(parseFloat(pad));
    const new_height = $content.scrollHeight + pad_px;
    if (new_height != view_options.input_row_height) {
      view_options.input_row_height = new_height;
      on_room_ready(view_options_apply);
    } else {
      $inputrow.style.flexBasis = old_flexBasis;
    }
  }

  /*
  if (embed) {
    // make the send/poke button smaller
    const $send_icon = $("#send > svg");
    $send_icon.classList.add("i35");
    $send_icon.classList.remove("i40");
  }
  */

  // save input content to local storage for this room in case of page reload, etc
  save_content();
}

function save_content() {
  const content = $content.value;
  const key = "content_" + room;
  if (content) {
    localStorage.setItem(key, content);
  } else {
    localStorage.removeItem(key);
  }
}

function restore_content() {
  // restore input content from local storage
  if ($content.value)
    return;
  const key = "content_" + room;
  const content = localStorage.getItem("content_" + room);
  if (content)
    $content.value = content;
}

function content_keydown(ev) {
  auto_play_back_off();
}

// change room ---------------------------------------------------------------

function messages_iframe_set_src(url) {
  $messages_iframe.contentWindow.location.replace(url);
  room_ready = false;
}

function help_iframe_set_src(url) {
  $id("help-frame").contentWindow.location.replace(url);
}

function reload_messages() {
  reload_page();
  // because the following does not work reliably...
  // clear_messages_box();
  // setTimeout(() => set_room(), 1);
}

export function clear_messages_box() {
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

export async function set_room(room_new, no_history) {
  // check if room_new was passed
  if (room_new === undefined) {
    $room.value = $room.value.trim();
    room_new = $room.value;
  }

  // check if we're already in the room
  if (room === room_new) {
    // console.log("already in room", room);
    active_reset("room_ops_move");
    active_reset("room_ops_copy");
    focus_content_on_pc();
    return;
  }

  // check for nsfw room in wrong case
  const room_new_lc = room_new.toLowerCase();
  if (room_new_lc == "nsfw" || room_new_lc.startsWith("nsfw/"))
    room_new = "nsfw" + room_new.slice(4);

  is_private = room_new.startsWith(user + "/");
  is_nsfw = is_private || room_new.startsWith("nsfw/");

  $body.classList.toggle("private", is_private);
  $body.classList.toggle("nsfw_zone", is_nsfw);

  // check if we're moving / copying a room or file
  if (active_get("room_ops_move") || active_get("room_ops_copy")) {
    const mode = active_get("room_ops_move") ? "move" : "copy";
    if (room_new = await move(room, room_new, mode)) {
      active_reset("room_ops_move");
      active_reset("room_ops_copy");
      // continue browsing to the new name, will do a reload unfortunately
    } else {
      // move / copy was rejected
      $room.value = room;
      error(`room_ops_${mode}`);
      // stay in move / copy mode
      select_room_basename();
      return;
    }
  }

  const type = get_file_type(room_new);

  if (type != "room")
    $body.classList.remove("empty");

//  if (view === "view_edit" && type == "dir" && !edit_close()) {
//    // reject browsing to a directory if we have unsaved changes in the editor
  if (view === "view_edit" && !edit_close()) {
    // reject browsing if we have unsaved changes in the editor
    $room.value = room;
    history.forward();  // typically we would get here from the back button?  and this doesn't hurt if not
    error("room");
    return;
  }

  room = $room.value = room_new;
  set_title_hash(room, no_history);
  $id("nav").href = location.pathname + location.hash;

  clear_messages_box();
  if (!room) return;

  if (type == "room") {
    try {
      await get_options();  // can throw if access denied
    } catch {
      await setup_all_link_buttons();
      return;
    }
  }

  // who();

  access_denied = false;

  await setup_all_link_buttons();
  setup_admin();

  nsfw_zone_room_changed();

  // if (view === "view_edit" && !edit_changed()) {
  //   // just change room, exit the editor
  //   view = "messages";
  if (view === "view_edit") {
    editor_file = room_new;
    if (type == "room")
      editor_file += EXTENSION;
    editor_text_orig = null;
  } else if (type == "file") {
    // start editing the file
    edit(room_new);
  }

  if (view !== "view_edit") {
    reset_ui();
    // if (view_options.advanced)
    //   set_top("top_scroll");
  }

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

async function setup_all_link_buttons() {
//  setup_help_links();
  setup_user_button();
  await setup_nav_buttons();
  show_room_privacy();
}

function show_room_privacy() {
  const $privacy = $id("privacy");
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
    $privacy.href = "/" + query_to_hash(PUBLIC_ROOM);
  } else {
    $privacy.href = "/" + query_to_hash(user + "/chat");
  }
}

/*
function setup_help_links() {
  const show_nsfw = room.startsWith("nsfw/") && !access_denied;
  const $help_links = $id("help-widget-links");
  show("intro_link", !show_nsfw);
  show("intro_link_nsfw", show_nsfw);
  show("guide_nsfw", show_nsfw);
}
*/

// move or copy a room or file -----------------------------------------------------

function move_mode(mode) {
  if (typeof mode === "object")
    mode = null;
  mode = mode || "move";
  // button was clicked, toggle move mode
  if (active_toggle(`room_ops_${mode}`)) {
    select_room_basename();
  } else {
    focus_content_on_pc();
  }
}

function copy_mode() {
  return move_mode("copy");
}

async function move(source, dest, mode) {
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
  formData.append("mode", mode);

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

// send a message to the room iframe -----------------------------------------

function send_to_room_iframe(message) {
  on_room_ready(() => {
    $messages_iframe.contentWindow.postMessage(message, ROOMS_URL);
  })
}

function send_to_help_iframe(message) {
  $id("help-frame").contentWindow.postMessage(message, ALLYCHAT_CHAT_URL);
}

// navigation ----------------------------------------------------------------

function nav_click(ev) {
  if (event.button !== 0 || event.shiftKey || event.ctrlKey || event.altKey || event.metaKey)
    // let the browser do the default action, e.g. open this same page in another tab
    return true;
  ev.preventDefault();
  set_top_left("top_left_nav");
}

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
  if(!editor_file) {
    send_to_room_iframe({ type: "scroll_home_end", p });
  } else
    $edit.scrollTop = p * $edit.scrollHeight;
}

function scroll_pages(ev, d) {
  ev.preventDefault();
  if(!editor_file) {
    send_to_room_iframe({ type: "scroll_pages", d });
  } else
    $edit.scrollTop += d * $edit.clientHeight;
}

// pages ---------------------------------------------------------------------

function pages_click(ev) {
  if (ev.button !== 0 || ev.shiftKey || ev.ctrlKey || ev.altKey || ev.metaKey)
    // let the browser do the default action, e.g. open this same page in another tab
    return true;
  ev.preventDefault();
  set_top_left("top_left_pages");
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
  const now = Date.now();  /* XXX this is not ideal */
  const $old_link = $id("theme");
  const $new_link = $old_link.cloneNode();
  if (theme) {
    $new_link.href = "/themes/" + theme + ".css?_=" + now;
  } else {
    $new_link.href = "/users/" + user + "/theme.css?_=" + now;
  }
  $new_link.id = "theme";
  $on($new_link, "load", theme_loaded);
  $old_link.replaceWith($new_link);
}

async function load_user_files() {
  const user_dir = "/users/" + user;
  const [_, userScript, nag_response] = await Promise.all([
    $style("user_styles", user_dir + "/styles.css"),
    $import("user_script", user_dir + "/script.js"),
    fetch(user_dir + "/nag.html?" + Date.now()), // prevent caching
  ]);
  let nag = nag_response.ok ? await nag_response.text() : "";
  // title case
  const name = user.replace(/\b./g, c => c.toUpperCase());
  nag = nag.replace(/\$USER\b/g, encode_entities(name));
  setup_system_message(nag);

//  modules.user_script = userScript; // XXX isn't that automatic?
}

// hash change ---------------------------------------------------------------

let new_hash = "";
let new_title = "";

function query_to_title(query) {
  return query;
}

function query_encode(query) {
  return encodeURIComponent(query).replace(/%20/g, "+").replace(/%2F/g, "/");
}

function query_to_hash(query) {
  return "#" + query_encode(query);
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
  $title.innerText = query_to_title(hash_to_room(location.hash));
  let h = location.hash;
  if (h == "" || h == "#") {
    h = "#" + DEFAULT_ROOM;
  }
  if (h == "#-" && h != new_hash) {
    clear_messages_box();
  }
  if (h != new_hash) {
    let query = hash_to_room(h);
    $room.value = query;
    set_room();
  }
}

function hash_to_room(hash) {
  let query = hash.replace(/\+|%20/g, " ");
  if (query.length)
    query = query.substr(1);
  // replace #.* with empty string
  query = decodeURIComponent(query);
  query = query.replace(/#.*/, "");
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
    // folder view, don't select the folder
    return;
    // // If ends with /, find the previous slash
    // const previousSlashIndex = value.lastIndexOf('/', lastSlashIndex - 1);
    // if (previousSlashIndex !== -1) {
    //   // If there's a previous slash, select from there to end
    //   start = previousSlashIndex + 1;
    // }
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

  // escape from the full-screen canvas! or any canvas
  if (view_options.canvas > 0) {
    view_options.canvas--;
    view_options_apply();
    return;
  }

  let acted = false;
  if (active_get("room_ops_move") || active_get("room_ops_copy")) {
    $room.value = room;
    active_reset("room_ops_move");
    active_reset("room_ops_copy");
    focus_content_on_pc();
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
  const room_enc = query_encode(room);
  const response = await fetch(`/x/last?room=${room_enc}`);
  if (!response.ok)
    return null;
  const data = await response.json();
  if (data.error)
    return null;
  return room_set_number(+data.last + i);
}

// Keyboard shortcuts --------------------------------------------------------

export const shortcuts = {};

function shortcuts_clear() {
  shortcuts.global = {};
  shortcuts.message = {};
  shortcuts.room = {};
  shortcuts.filter = {};
  shortcuts.edit = {};
};

shortcuts_clear();

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
  if (key !== "alt" && ev.altKey)
    view_option_skip_alt = true;
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

  if (shortcut && !ev.repeat) {
    ev.preventDefault();
    shortcut.fn(ev);
    return true;
  }
  return false;
}

function setup_main_ui_shortcuts() {
  add_shortcuts(shortcuts.global, [
    ['escape', escape, 'Go back, change or leave room'],
  ]);

  add_shortcuts(shortcuts.message, [
    ['ctrl+enter', () => send(), 'Send message'],
  ]);

  // simple mode
  if (view_options.advanced < 0) {
    if (!isMobile) {
      add_shortcuts(shortcuts.message, [
        ['enter', () => send(), 'Send message'],
      ]);
    }
    // return;
    // will try with all shortcuts in simple mode too...
  }

  add_shortcuts(shortcuts.global, [
    ['ctrl+;', change_room, 'Change room'],
    ["ctrl+[", () => set_room(room_first()), "Go to first room"],
    ['ctrl+.', () => set_room(room_next()), 'Go to next room'],
    ['ctrl+,', () => set_room(room_prev()), 'Go to previous room'],
    ['ctrl+]', async () => set_room(await room_last()), 'Go to last room'],
    ['ctrl+\\', async () => set_room(await room_last(1)), 'Go beyond last room'],
  ]);

  add_shortcuts(shortcuts.message, [
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
    ['shift+alt+c', copy_mode, 'Copy mode', ADMIN],

    ['alt+z', undo, 'Undo last message', ADMIN],
    ['ctrl+alt+z', (ev) => undo(ev, true), 'Erase last message', ADMIN],
    ['alt+r', retry, 'Retry last action', ADMIN],
    ['ctrl+alt+r', (ev) => retry(ev, true), 'Retry last action', ADMIN],
    ['alt+x', clear_chat, 'Clear messages', ADMIN],
    ['shift+alt+a', archive_chat, 'Archive chat', ADMIN],
//    ['shift+alt+c', clean_chat, 'Clean up the room', ADMIN],
    ['alt+e', () => edit(), 'Edit file', ADMIN],
    ['alt+h', rerender_html, 'Re-render HTML', ADMIN],

    ['alt+n', () => invoke(narrator), 'Invoke the narrator'],
    ['alt+v', () => invoke(illustrator), 'Invoke the illustrator'],
    ['alt+/', () => invoke("anyone"), 'Invoke anyone randomly'],
    ['shift+alt+/', () => invoke("everyone"), 'Invoke everyone'],
    ['ctrl+alt+a', (ev) => content_insert(ev, "α"), 'Insert alpha: α'],
  ]);

  add_shortcuts(shortcuts.room, [
    ['enter', focus_content, 'Focus message input'],
    ['shift+alt+m', move_mode, 'Move mode', ADMIN],
    ['shift+alt+c', copy_mode, 'Copy mode', ADMIN],
  ]);

  add_shortcuts(shortcuts.filter, [
    ['enter', filter_changed, 'Change image filter'],
  ]);

  add_shortcuts(shortcuts.edit, [
    ['alt+t', edit_indent, 'Insert tab / indent'],
    ['shift+alt+t', edit_dedent, 'dedent'],
    ['escape', edit_close_back, 'Close edit'],
    ['ctrl+s', edit_save, 'Save edit'],
    ['ctrl+enter', edit_save_and_close, 'Save edit and close'],
    ['alt+z', edit_reset, 'Reset edit'],
    ['alt+x', edit_clear, 'Clear edit'],
  ]);
}

// handle messages from the messages iframe ----------------------------------

function handle_message(ev) {
		// FIXME, too much power for scripts in the room?
  if (embed && ev.origin == ALLYCHAT_CHAT_URL) {  /* TODO support other host sites */
    if (ev.data.type == "theme_changed")
      return set_theme(ev.data.theme);
    if (ev.data.type == "set_view_options") {
      delete ev.data.type;
      return set_view_options(ev.data);
    }
    if (ev.data.type == "op") {
      if (ev.data.op == "undo")
        return undo();
      if (ev.data.op == "retry")
        return retry();
      if (ev.data.op == "archive")
        return archive_chat();
      if (ev.data.op == "clear")
        return clear_chat();
    }
  }
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

  if (ev.data.type == "status") {
    update_room_status(ev.data);
    return;
  }

  if (ev.data.type == "copy") {
    // copy to clipboard
    try {
      let text = ev.data.text;
      navigator.clipboard.writeText(text);

      // check if spans multiple lines
      const multiline = text.match(/\n/);

      // if a likely name, ends with , and not multiline FIXME
      // put it in the input box
      const paste_to_input = text.endsWith(",") && !multiline;
      if (paste_to_input) {
        $content.focus();

        const sep = multiline ? "\n" : " ";

        const old = $content.value;
        const selStart = $content.selectionStart;
        const beforeChar = selStart > 0 ? old.charAt(selStart - 1) : sep;
        const afterChar = selStart < old.length ? old.charAt(selStart) : '';

        if (beforeChar !== sep)
          text = sep + text;
        if (afterChar !== sep && !text.endsWith(sep))
          text += sep;

        document.execCommand('insertText', false, text);
        message_changed();
      }
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
    $content.placeholder = ""; // it interferes with the overlay in Chrome
  } else {
    $messages_iframe.classList.remove("overlay");
  }
}

// authentication ------------------------------------------------------------

function logout_confirm(ev) {
  ev.preventDefault();
  if (confirm_except_iOS("Log out?"))
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
  return userData;
}

// set the user button text and href -----------------------------------------

function setup_user_button() {
  const $user = $id("user");
  $user.innerText = user;
  // go from main directory to public room
  if (room == "/") $user.href = "/" + query_to_hash(PUBLIC_ROOM);
  // go from public user chat to main directory
  else if (room == user) $user.href = "/" + query_to_hash("/")
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
  let room_up;
  if (room == "/") {
    room_up = DEFAULT_ROOM;
  } else if (room.match(/\/$/)) {
    room_up = room.replace(/[^\/]*\/$/, "");
    if (room_up == "") {
      room_up = "/";
    }
  } else {
    room_up = room.replace(/[^\/]+$/, "") || "/";
  }
  $nav_up.href = "/" + query_to_hash(room_up);

  // Setup allychat button --------------------
  const $nav_allychat = $id("nav_allychat");
  $nav_allychat.href = "/" + query_to_hash(PUBLIC_ROOM);

  // Setup nsfw buttons --------------------
  for (const $nav_nsfw of $$(".nav_nsfw")) {
    $nav_nsfw.href = "/" + query_to_hash(is_nsfw ? PUBLIC_ROOM : NSFW_ROOM);
    $nav_nsfw.title = is_nsfw ? "Go to the main SFW room: "+PUBLIC_ROOM : "Go to the main NSFW room: "+NSFW_ROOM;
  }

  // Setup porch button --------------------
  const $nav_porch = $id("nav_porch");
  $nav_porch.href = "/" + query_to_hash(user);

  // Setup home button --------------------
  const $nav_home = $id("nav_home");
  $nav_home.href = "/" + query_to_hash(user + "/chat");

  // Setup first room button --------------------
  const $pages_first = $id("pages_first");
  const pages_first_query = room_first();
  if (pages_first_query) {
    $pages_first.href = query_to_hash(pages_first_query);
  } else {
    $pages_first.removeAttribute("href");
  }

  // Setup prev room button --------------------
  const $pages_prev = $id("pages_prev");
  const roomPrev = room_prev();
  if (roomPrev) {
    $pages_prev.href = "/" + query_to_hash(roomPrev);
  } else {
    $pages_prev.removeAttribute("href");
  }

  // Setup next room button --------------------
  const $pages_next = $id("pages_next");
  const roomNext = room_next();
  if (roomNext) {
    $pages_next.href = "/" + query_to_hash(roomNext);
  } else {
    $pages_next.removeAttribute("href");
  }

  // Setup last room button --------------------
  // TODO this is heavy, avoid unless clicked?
  const $pages_last = $id("pages_last");
  const roomLast = await room_last();
  if (roomLast) {
    $pages_last.href = "/" + query_to_hash(roomLast);
  } else {
    $pages_last.removeAttribute("href");
    access_denied = true;
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
  upload_files(files, true);  // in the background
  ev.target.value = "";
  // set_controls();
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

export async function add_upload_file_link(promise) {
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

export async function upload_file(file, filename, to_text) {
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
  // experiment: allow anyone who can write to moderate
  admin = true;
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
  else if (op === "archive" && CONFIRM_ARCHIVE)
    confirm_message = "Archive the chat?  You can go to it later with ctrl-].";
  else if (op == "clean")
    confirm_message = "Clean up the room?  Removes messages from specialists.";
  else if (op == "render")
    confirm_message = null;
  // TODO it would be better to hide them from everyone, with a switch
  // else
  //   throw new Error("invalid op: " + op);

  if (confirm_message && !confirm_except_iOS(confirm_message)) return;

  if (ev)
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

  $body.classList.add("empty");

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
  if (ev)
    ev.preventDefault();

  hard = hard || (ev && ev.ctrlKey);
  auto_play_back_off();

  if (!(ev && (ev.key || ev.shiftKey) || confirm_except_iOS("Undo the last message?\n(hold shift to skip this confirmation next time, or use keyboard shortcuts)")))
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
    active_dec("send");  // FIXME this is wonky
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

export function set_controls(id) {
  id = id || "input_main";
  const $el = $id(id);
  if ($el.classList.contains("hidden")) {
    hide($("#inputrow > .controls:not(.hidden)"));
    show($id(id));
  }
  if (id === "input_main") {
    setTimeout(() => focus_content_on_pc());
  }
  if (id === "input_view") {
    if (view_theme_original_text) {
      $id("view_theme").textContent = view_theme_original_text;
    } else {
      view_theme_original_text = $id("view_theme").textContent;
    }
    $on($id("view_theme"), "mouseover", show_theme_name);
    $on($id("view_theme"), "touchstart", show_theme_name);
  }
  controls = id;
  focus_content_on_pc();
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
  if (!isMobile && id == "top_filter")
    $id('filter_query').focus();
  else
    focus_content_on_pc();
}

function set_top_left(id) {
  id = id || "top_left_main";
  const $el = $id(id);
  if ($el.classList.contains("hidden")) {
    hide($("#top > .top_left_controls:not(.hidden)"));
    show($el);
  }
  top_controls = id;
  focus_content_on_pc();
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
  controls_resized();
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
  // default to messages view
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

function edit_changed() {
  return edit_get_text() !== editor_text_orig;
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
    active_dec("edit_save");
    await error("edit_save");
    return false;
  }

  active_dec("edit_save");
  return true;
}

async function edit_save_and_close() {
  if (await edit_save())
    edit_close_back();
}

function edit_reset() {
  if (edit_changed())
    if (!confirm_except_iOS("Discard changes?")) return;
  edit_set_text(editor_text_orig);
}

function edit_clear() {
  edit_set_text("");
}

function edit_close_back() {
  // if ends with EXTENSION, strip it off
  const stem = editor_file.replace(new RegExp(quotemeta(EXTENSION)+"$"), "");
  const type = get_file_type(stem);
  if (edit_close() && type == "file") {
    // if can't go back, go to parent folder
    if (history.length > 1)
      history.back();
    else
      nav_up();
  }
}

function edit_close(ev) {
  if (ev)
    ev.stopPropagation();
  if (edit_changed())
    if (!confirm_except_iOS("Discard changes?")) return false;
  // const type = get_file_type(editor_file);
  // // const leafname = editor_file.replace(/.*\//, "");
  // let dirname;
  // // check if '/' in editor_file
  // if (editor_file.includes("/"))
  //   dirname = editor_file.replace(/\/[^\/]*$/, "") + "/";
  // else
  //   dirname = "/";
  // // const dont_change = ["access.yml", "options.yml"];
  // // let change_to_room = type == "file" && !dont_change.includes(leafname) && editor_file.replace(/\.[^\/]*$/, "");

  // let change_to_room;
  // if (type == "file" && editor_file.endsWith(EXTENSION))
  //   change_to_room = editor_file.replace(/\.[^\/]*$/, "");
  // else
  //   change_to_room = dirname;

  editor_text = editor_text_orig = null;
  editor_file = null;
  $edit.value = "";
  set_view();
  set_controls();

  // if (change_to_room)
  //   set_room(change_to_room);
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
    simple = view_options.advanced < 0;
  }
  if (embed) {
    for (const key in view_options_embed) {
      view_options[key] = view_options_embed[key];
    }
  }
  set_default_room();
  on_room_ready(view_options_apply);
}

function set_default_room() {
  if (simple)
    DEFAULT_ROOM = user + "/chat";
  else
    DEFAULT_ROOM = PUBLIC_ROOM;
}

function set_view_options(new_view_options) {
  for (const key of Object.keys(new_view_options))
    view_options[key] = new_view_options[key];
  view_options_apply();
}

function view_options_apply() {
  const type = get_file_type(room);
  simple = view_options.advanced < 0;

  set_default_room();

  // temporarily avoid simple mode! XXX
  // if (view_options.advanced < 0)
  //   view_options.advanced = 0

  // includes audio options
  // save to local storage
  if (!embed)
    localStorage.setItem("view_options", JSON.stringify(view_options));

  // Reset UI in simple mode
  if (simple) {
    set_top();
    set_top_left();
    set_controls();
    set_view();
    $body.classList.remove("option");
  }

  // Don't allow boffin mode except for devs and early-access users
  if (!dev && !early && view_options.advanced >= 2)
    view_options.advanced = 1;

  // Don't allow full-screen canvas except in boffin mode:
  // It makes it look like the app is broken!
  if (view_options.canvas == 2 && view_options.advanced < 2)
    view_options.canvas = 1;

  // view TOC contradicts view canvas
  if (view_options.toc)
    view_options.canvas = 0;

  // update buttons
  // TODO simplify / de-dup this code
  active_set("view_ids", view_options.ids);
  active_set("view_images", view_options.images);
  active_set("view_alt", view_options.alt);
  active_set("view_source", view_options.source);
  active_set("view_highlight", view_options.highlight);
  active_set("view_details", view_options.details);
  active_set("view_canvas", view_options.canvas);
  active_set("view_toc", view_options.toc);
  active_set("view_clean", view_options.clean);
  active_set("view_image_size", view_options.image_size - image_size_default);
  active_set("view_font_size", view_options.font_size - font_size_default);
  active_set("view_columns", view_options.columns);
  active_set("view_compact", view_options.compact);
  active_set("view_history", view_options.history);
  active_set("view_fullscreen", view_options.fullscreen);
  $id("view_items").value = view_options.items ?? "";
  active_set("view_advanced", view_options.advanced > 1);
  active_set("view_standard", view_options.advanced >= 0);
  $inputrow.style.flexBasis = view_options.input_row_height + "px";
  active_set("audio_stt", view_options.audio_stt);
  active_set("audio_tts", view_options.audio_tts);
  active_set("audio_vad", view_options.audio_vad);
  active_set("audio_auto", view_options.audio_auto);

  active_set("help", view_options.help > 0);
  $id("help").href = view_options.advanced ? qa_url : help_url;

  // show different simple / advanced / boffin icons
  const $view_advanced = $id("view_advanced");
  const $view_standard = $id("view_standard");
  if (view_options.advanced == -1) {
    $view_standard.innerHTML = icons["view_mode_simple"]
    $view_standard.title = "simple mode: click for standard mode";
  } else if (view_options.advanced == 0) {
    $view_advanced.innerHTML = icons["view_mode_not_advanced"]
    $view_standard.innerHTML = icons["view_mode_standard"]
    $view_advanced.title = "standard mode: click for advanced mode";
    $view_standard.title = "standard mode";
  } else if (view_options.advanced == 1) {
    // $view_advanced.innerHTML = icons["view_mode_advanced"]
    $view_advanced.innerHTML = icons["view_mode_boffin_off"]
    $view_advanced.title = "advanced mode";
  } else {
    $view_advanced.innerHTML = icons["view_mode_boffin"]
    $view_advanced.title = "boffin mode";
  }

  $id("audio_voice").value = view_options.audio_voice;

  const cl = document.body.classList;
  cl.toggle("simple", view_options.advanced == -1);
  cl.toggle("standard", view_options.advanced == 0);
  cl.toggle("advanced", view_options.advanced == 1);
  cl.toggle("boffin", view_options.advanced >= 2);
  cl.toggle("compact", view_options.compact >= 1);
  cl.toggle("compact2", view_options.compact == 2);
  cl.toggle("embed", embed);

  // help embed
  show("help-widget", view_options.help > 0);
  if (view_options.help) {
    let i = 1;
    for (const $l of [...$$("#help-widget-header a")].filter(is_showing)) {
      $l.classList.toggle("link_active", i == view_options.help);
      if (i == view_options.help)
        help_iframe_set_src($l.href);
      ++i;
    }

    ensure_embed_scripts();
  } else {
    // help_iframe_set_src("");
  }

  // input placeholder in standard mode, before first message sent in this session
  let input_placeholder = "";
  let hold_or_press = hold_alt ? "Hold" : "Press";
  if (simple && $content.placeholder != "") {
    if (isMobile)
      input_placeholder += `Long-press here for options.`;
    else
      input_placeholder += `${hold_or_press} ${Alt} for options.`;
  } else if (simple) {
    $content.placeholder = " ";
  } else if ($content.placeholder != "" && view_options.advanced == 0) {
    if (!isMobile)
      input_placeholder += "Ctrl+Enter to Send. ";
    // input_placeholder += "Send an empty message to Poke the chat. ";
    if (isMobile)
      input_placeholder += "Long-press for simple mode.";
    else
      input_placeholder += `${Alt} for simple mode.`;
    input_placeholder += " { } for prompts.";
  }
  $content.placeholder = input_placeholder;
  if (input_placeholder != "")
    setTimeout(() => { $content.placeholder = ""; }, 10000);

  if (view_options.image_size >= 10)
    view_image_size_delta = -1;
  if (view_options.image_size <= 1)
    view_image_size_delta = 1;
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

  const zoom = 1.15**(view_options.font_size-font_size_default);
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

  // show dir sort
  if (type === "dir") {
    const sort_icon = "sort_" + view_options.dir_sort;
    const $dir_sort = $id("dir_sort");
    $dir_sort.innerHTML = icons[sort_icon];
    $dir_sort.title = "sort: " + view_options.dir_sort;
  }
  show("dir_sort", type === "dir");
  show("pages", type !== "dir");

  // send message to the rooms iframe to apply view options
  send_to_room_iframe({ type: "set_view_options", ...view_options });

  controls_resized();
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
  const delta = ev.shiftKey || ev.ctrlKey ? -1 : 1;
  view_options.images = (view_options.images + delta + 3) % 3;
  view_options_apply();
}

function view_alt(ev) {
  view_options.alt = !view_options.alt;
  view_options_apply();
}

function view_source(ev) {
  const delta = ev.shiftKey || ev.ctrlKey ? -1 : 1;
  if (view_options.advanced)
    view_options.source = (view_options.source + delta + 4) % 4;
  else
    view_options.source = view_options.source ? 0 : 2;
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
  // view canvas contradicts view toc
  if (view_options.canvas)
    view_options.toc = 0;
  view_options_apply();
}

function view_toc(ev) {
  view_options.toc = !view_options.toc;
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
  const delta = ev.shiftKey || ev.ctrlKey ? -1 : 1;
  view_options.compact = (view_options.compact + delta + 3) % 3;
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

function dir_sort(ev) {
  ev.preventDefault();
  view_options.dir_sort = view_options.dir_sort === "alpha" ? "time" : "alpha";
  view_options_apply();
}

function view_advanced(ev) {
  // -1 simple  (not from this button)
  // 0 standard - skip this now
  // 1 advanced
  // 2 boffin
  const delta = ev.shiftKey || ev.ctrlKey ? -1 : 1;
  const max = (dev||early) ? 3 : 2;
  view_options.advanced = (view_options.advanced + delta + max) % max;
  if (view_options.advanced == 0)
    view_options.advanced = (view_options.advanced + delta + max) % max;
  view_options_apply();
}

function view_standard(ev) {
  // -1 simple
  // 0 standard - skip this now
  // 1 advanced
  view_options.advanced = view_options.advanced >= 0 ? -1 : 1;
  if (view_options.advanced >= 0)
    view_option_skip_alt = true;
  else
    view_options_reset();
  view_options_apply();
  shortcuts_clear();
  setup_main_ui_shortcuts();
  message_changed();
}

function clamp(num, min, max) { return Math.min(Math.max(num, min), max); }

function view_image_size(ev) {
  // range from 1 to 10
  const reset = ev.ctrlKey;
  if (reset || ev.shiftKey)
    view_image_size_delta = 1;
  if (reset) {
    view_options.image_size = image_size_default;
  } else {
    const neg = ev.shiftKey ? -1 : 1;
    const delta = neg * view_image_size_delta;
    // view_options.image_size = ((view_options.image_size || image_size_default) + delta + 9) % 10 + 1;
    view_options.image_size = clamp((view_options.image_size || image_size_default) + delta, 1, 10);
  }
  view_options_apply();
}

function view_font_size(ev) {
  // range from 1 to 10
  const reset = ev.ctrlKey;
  if (reset) {
    view_options.font_size = font_size_default;
    view_font_size_delta = 1;
  } else {
    const neg = ev.shiftKey ? -1 : 1;
    const delta = neg * view_font_size_delta;
    view_options.font_size = ((view_options.font_size || font_size_default) + delta + 9) % 10 + 1;
  }
  view_options_apply();
  if (!$id("help-widget").classList.contains("hidden"))
    send_to_help_iframe({ type: "set_view_options", font_size: view_options.font_size });
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
  // add current time ms
  const response = await fetch("/themes/?_=" + Date.now());  /* XXX not ideal */
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
  // basic and standard mode, just toggle light and dark
  if (simple) {
    theme = theme === "light" ? "dark" : "light";
    return set_theme(theme);
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
  set_theme(theme);
}

function set_theme(theme_new) {
  theme = theme_new;
  if (!embed)
    show_theme_name();
  set_settings({ theme: theme });
  load_theme();
  send_to_room_iframe({ type: "theme_changed", theme });

  // If help is open, reload it for the new theme
  if (!$id("help-widget").classList.contains("hidden"))
    send_to_help_iframe({ type: "theme_changed", theme });
}

let hide_theme_timeout;

function create_theme_overlay() {
  const overlay = document.createElement('div');
  overlay.id = 'theme-overlay';
  document.body.appendChild(overlay);
  return overlay;
}

function show_theme_name() {
  let overlay = $id('theme-overlay');
  if (!overlay) {
    overlay = create_theme_overlay();
  }

  overlay.textContent = theme;
  overlay.style.opacity = '1';

  clearTimeout(hide_theme_timeout);
  hide_theme_timeout = setTimeout(() => {
    overlay.remove();
    overlay = null;
  }, 1000);
}

// options -------------------------------------------------------------------

async function get_options() {
//  console.log("get_options", room);
  const query = new URLSearchParams({
    room,
  });
  const response = await fetch("/x/options?" + query, { cache: "no-cache" });
  if (!response.ok) {
    access_denied = true;
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
  const temp = data?.agents?.all?.temp ?? "";
  const mission = data?.mission === "" ? "-" : data?.mission ?? "";
  $id("opt_context").value = context;
  $id("opt_lines").value = lines;
  $id("opt_images").value = images;
  $id("opt_temp").value = temp;
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

async function opt_temp(ev) {
  let temp = ev.target.value;
  temp = temp === "" ? null : +temp;
  await set_options({
    room: room,
    options: {
      agents: {
        all: {
          temp
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


async function setup_icons() {
  await $import("icons");
  icons = modules.icons.icons;
  for (const prefix of ["mod", "add", "view", "opt", "nav", "pages", "scroll", "audio", "select", "room_ops"]) { //, "filter"]) {
    icons[`${prefix}_cancel`] = icons[prefix]; // icons["x"];
  }
//  icons["edit_close"] = icons["x"];
  for (const prefix of ["edit", "help"]) {
    icons[`${prefix}_close`] = icons[prefix];
  }
  // icons["edit_close"] = icons["edit"];
  icons["help_close"] = icons["x"]; // icons["help"];
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
//  icons["room_ops_move"] = icons["select_move"];
  icons["access_denied"] = icons["x_large"];
  icons["add_file_2"] = icons["add_file"];
  icons["font_contract"] = icons["font_expand"];
  icons["mod_auto"] = icons["auto"];
  icons["audio_auto"] = icons["auto"];

  icons["help_undo"] = icons["x_large"];
  icons["help_retry"] = icons["undo"];
  icons["help_archive"] = icons["mod_archive"];
  icons["mod_archive_2"] = icons["mod_archive"];
  icons["help_clear"] = icons["mod_clear"]

  icons["view_advanced"] = icons["view_mode_standard"]; // XXX check this
  icons["view_standard"] = icons["view_mode_simple"];

//  icons["room_ops_copy"] = icons["copy"];  // TODO remove this
  icons["select_copy"] = icons["copy"];

  icons["filter_2"] = icons["filter"];
  icons["scroll_end_2"] = icons["scroll_end"];

  for (const id in icons) {
    let el = $id(id);
    if (el)
      setup_icon(id, el);
    else
      for (el of $$("."+id))
        setup_icon(id, el);
  }
}

function setup_icon(id, el) {
  const text = el.textContent;
  el.title = el.title || text;
  el.innerHTML = icons[id];
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

// embedding e.g. help overlay -----------------------------------------------

function setup_embed_vs_main_ui() {
  if (embed)
    return setup_embed_ui();
  return setup_main_ui();
}

function setup_main_ui() {
  // show all UI controls
  show("top");
  show("inputrow");
  setup_main_ui_shortcuts();
}

function setup_embed_ui() {
  // hide main controls other than the send button
  for (const $e of $$("#input_main > button:not(#send)"))
    hide($e);
  show("inputrow");

  add_shortcuts(shortcuts.message, [
    ['ctrl+enter', () => send(), 'Send message'],
    ['alt+z', undo, 'Undo last message', ADMIN],
    ['ctrl+alt+z', (ev) => undo(ev, true), 'Erase last message', ADMIN],
    ['alt+r', retry, 'Retry last action', ADMIN],
    ['ctrl+alt+r', (ev) => retry(ev, true), 'Retry last action', ADMIN],
    ['alt+x', clear_chat, 'Clear messages', ADMIN],
    ['shift+alt+a', archive_chat, 'Archive chat', ADMIN],
    ['alt+h', rerender_html, 'Re-render HTML', ADMIN],
  ]);
  return;
}

// help and info -------------------------------------------------------------

function setup_help() {
  help_room = `${user}/help`;
  qa_room = `${user}/qa`;
  help_url = ALLYCHAT_CHAT_URL + `/#${help_room}`;
  qa_url = ALLYCHAT_CHAT_URL + `/#${qa_room}`;
  $id("help_link").href = help_url;
  $id("qa_link").href = qa_url;

  $on($id("help"), "click", help_click);

  $on($id("help_close"), "click", () => help_click());
  $on($id("help_undo"), "click", () => help_op("undo"));
  $on($id("help_retry"), "click", () => help_op("retry"));
  $on($id("help_archive"), "click", () => help_op("archive"));
  $on($id("help_clear"), "click", () => help_op("clear"));

  for (const $e of $$("#help-widget-header a")) {
    $on($e, "click", handleHelpLinkClick);
  }
}

async function help_click(ev) {
  // if shift, ctrl pressed, do the default action
  if (ev && (ev.shiftKey || ev.ctrlKey))
    return;
  if (ev)
    ev.preventDefault();
  // if alt pressed, open in this window
  if (ev && (ev.altKey)) {
    await set_room(view_options.advanced > 0 ? qa_room : help_room);
    return;
  }
  // for normal click, we open a magic embedded chat on the help room!!
  view_options.help = view_options.help ? -view_options.help : 1;
  view_options_apply();
}

function help_op(op) {
  send_to_help_iframe({ type: "op", op: op });
}

async function ensure_embed_scripts() {
  await Promise.all([
    $script("script_embed", "/embed.js"),
    $style("style_embed", "/embed.css"),
  ]);
}

function handleHelpLinkClick(event) {
  const linkElement = this;
  const targetHref = linkElement.href;

  if (event.shiftKey || event.ctrlKey)
    return true;

  event.preventDefault();

  if (event.altKey) {
    window.top.location.href = targetHref;
    return false;
  }

  let i = 1;
  for (const $l of [...$$("#help-widget-header a")].filter(is_showing)) {
    if ($l === linkElement && i != view_options.help) {
      view_options.help = i;
      view_options_apply()
      break;
    }
    ++i;
  }

  const targetIframe = $id('help-frame');
  targetIframe.contentWindow.location.replace(targetHref);

  return false;
}

// controls layout hack; Firefox and Safari don't do flex wrap properly ------

function controls_resized(entry) {
  // if (!(isFirefox || isSafari))
  //   return;
  if (!entry) {
    for (const controls of $$(".controls"))
      controls_resized({target: controls})
    return;
  }
  const $controls = entry.target;
  $controls.style.removeProperty("width");
  $controls.style.width = $controls.scrollWidth + 'px';
}

function controls_layout_hack_for_firefox_and_safari() {
  const observer = new ResizeObserver((entries) => entries.forEach(controls_resized));
  for (const controls of $$(".controls"))
    observer.observe(controls);
}

// iOS hack to reload on pull down -------------------------------------------

let do_reload = false;

function iOS_reload_scroll(ev) {
  // $id("debug").textContent = -window.scrollY;
  const $reload_icon = $id("reload_icon");
  if (do_reload && window.scrollY >= -50) {
    reload_page();
  } else if (window.scrollY < -100) {
    do_reload = true;
    $reload_icon.firstChild.style.color = "#7f7";
  } else if (window.scrollY < -10) {
    show($reload_icon);
    const rotation = Math.min(2 * (-window.scrollY-10), 360);
    $reload_icon.style.transform = `translateX(-50%) rotate(${rotation}deg)`;
  } else {
    hide($reload_icon)
  }
}

// selection -----------------------------------------------------------------

function select_click(ev) {
  set_top_left("top_left_select");
  mode_options.select = true;
  send_to_room_iframe({ type: "set_mode_options", ...mode_options });
}

function select_cancel(ev) {
  set_top_left();
  mode_options.select = false;
  send_to_room_iframe({ type: "set_mode_options", ...mode_options });
}

// filter images -------------------------------------------------------------

function load_filter() {
	view_options.filter = localStorage.getItem('filter') || '';
  $id('filter_query').value = view_options.filter;
}

function save_filter() {
	localStorage.setItem('filter', view_options.filter);
}

function filter_changed(ev) {
  // console.log("filter_changed");
  view_options.filter = $id('filter_query').value;
	save_filter();
  view_options_apply();
}

/* system messages -------------------------------------------------------- */

async function setup_system_message(nag) {
  if (!nag)
    return;
  const system_message = $id('system_message');
  system_message.innerHTML = nag;
  show(system_message);
  $on(system_message, 'click', () => dismiss_system_message());
}

function dismiss_system_message() {
  $id('system_message').remove();
}

/* NSFW Zone warning overlay ---------------------------------------------- */

let nsfw_zone_gate_delay_timeout;

export async function nsfw_zone_gate(show_it) {
  if (!show_it) {
    hide($id('nsfw-warning'));
    clearTimeout(nsfw_zone_gate_delay_timeout);
    nsfw_zone_gate_delay_timeout = null;
    return;
  }

  // localStorage.removeItem('nsfw_zone'); // XXX for testing
  const nsfwSetting = localStorage.getItem('nsfw_zone');

  // No action if already accepted
  if (nsfwSetting === "1")
    return;

  // Show overlay if not yet confirmed
  show($id('nsfw-warning'));
  $id('nsfw-warning').focus();

  // Encourage user to read the messages
  const btn = $id('nsfw-warning-yes');
  btn.disabled = true;

  const $$cb = Array.from($$('#nsfw-warning li input'));
  for (const $cb of $$cb) {
    $cb.checked = false;
    $cb.disabled = true;
    $on($cb, 'change', () => {
      const $em = $id($cb.id.replace('cb', 'em'));
      $em.classList.toggle("invisible", !$cb.checked);
      const all_checked = $$cb.every(cb => cb.checked);
      btn.disabled = !all_checked;
    });
  }

  const delay = 1000;

  const $$li = Array.from($$('#nsfw-warning li:not(:has(input))'));
  await $wait(delay);

  for (let i = 0; ; ++i) {
    if (i == $$li.length)
      break;
    const $li = $$li[i];
    $li.classList.add("highlight");
    const $em = $id($li.id.replace('con', 'em'));
    $em.classList.remove("invisible");
    await $wait(delay);
  }

  for (const $cb of $$cb)
    $cb.disabled = false;
}

export function nsfw_zone_set(accepted) {
  if (nsfw_zone_gate_delay_timeout)
    nsfw_zone_gate(false);

  // Show NSFW nav buttons if accepted
  for (const el of $$('a.nav_nsfw'))
    show(el, accepted !== "0");

  if (accepted == null)
    return localStorage.removeItem('nsfw_zone');

  localStorage.setItem('nsfw_zone', accepted);
  if (accepted !== "1") {
    // console.log("NSFW no");
    return go_home()
  }

  hide($id('nsfw-warning'));

  // console.log("NSFW yes");
}

export function nsfw_zone_init() {
  $on($id('nsfw-warning-no'), 'click', () => nsfw_zone_set("0"));
  $on($id('nsfw-warning-yes'), 'click', () => nsfw_zone_set("1"));
  // TODO show if room is NSFW and not yet accepted
  const nsfwSetting = localStorage.getItem('nsfw_zone');

  // Hide NSFW nav buttons if explicitly opted out
  if (nsfwSetting !== "0")
    for (const el of $$('a.nav_nsfw'))
      show(el);
}

export function nsfw_zone_room_changed() {
  const in_nsfw_zone = room.startsWith("nsfw/");
  nsfw_zone_gate(in_nsfw_zone);
}

// TODO remove export when no longer needed for testing

// Run on page load
// handleNSFWAccess();

// update room status --------------------------------------------------------

function update_room_status(data) {
  const $scroll_end_2 = $id("scroll_end_2");
  const scroll_icon = data.messages_at_bottom ? "scroll_home" : "scroll_end";
  const scroll_title = data.messages_at_bottom ? "start of room: home" : "end of room: end";
  $scroll_end_2.innerHTML = icons[scroll_icon];
  $scroll_end_2.title = scroll_title;
}

// view option ---------------------------------------------------------------

let view_option_skip_alt = false;

function view_option(ev) {
  // holding alt/option shows option controls in simple mode
  // pressing alt/option toggles option controls in other modes
  // if not in input_main controls, return to them and show options
  if (ev.key !== "Alt") // || view_options.advanced > 1)
    return;
  $content.placeholder = "";
  if (simple && hold_alt) {
    $body.classList.toggle("option", ev.type === "keydown");
  } else if (ev.type === "keyup" && controls == "input_main" && !view_option_skip_alt) {
    $body.classList.toggle("option");
  } else if (ev.type === "keyup" && controls !== "input_main" && !view_option_skip_alt) {
    set_controls();
    $body.classList.add("option");
  } else {
    view_option_skip_alt = false;
    return;
  }
  // prevent default action of moving focus to menu bar
  if (ev.type === "keyup")
    ev.preventDefault();
  controls_resized();
}

let long_press_timer;

function view_option_touchstart(event) {
  // Prevent default browser actions like text selection or context menu
  long_press_timer = setTimeout(() => {
    $body.classList.toggle("option");
    if ($body.classList.contains("option")) {
      set_controls();
      controls_resized();
    }
  }, 750); // 750ms is a common duration for long-press
}

function view_option_touchend() {
  clearTimeout(long_press_timer);
}

function setup_view_option_long_press() {
  $on($content, "touchstart", view_option_touchstart);
  $on($content, "touchend", view_option_touchend);
  //$on($content, "touchmove", view_option_touchend);
  $on($content, "touchcancel", view_option_touchend);
}

function hide_placeholder() {
  $content.placeholder = "";
}

// beta_test: put users' settings into a certain state for testing -----------

const beta_test_users = ["sam"]; // null for all

function beta_test() {
  const beta_test = view_options.beta_test;
  const done = view_options.beta_test_done;
  const do_beta = !beta_test_users || beta_test_users.includes(user);

  // console.log(`beta_test ${beta_test} done ${done}`);

  if (!do_beta)
    return;

  if (beta_test == done) {
    // console.log("beta_test already done");
    // pass
  } else if (beta_test == "simple2" && view_options.advanced >= 0) {
    // console.log("beta_test activated");
    view_options.source = 0;
    view_standard();
  } else {
    // console.log("beta_test not done");
    // unknown or obsolete beta test, remove it!
  }

  view_options.beta_test_done = beta_test;
  delete view_options.beta_test;
  view_options_apply();
}

// main ----------------------------------------------------------------------

export async function init() {
  const auth = await authChat();
  user = auth.username;
  nsfw = auth.nsfw;

  if (nsfw) {
    $body.classList.add("nsfw");
    nsfw_zone_init();
  }
  if (!isMobile)
    $body.classList.add("pc");

  if (iOS)
    document.body.classList.add("ios")

  setup_help();
  load_filter();
  setup_view_options();
  await setup_icons();
  setup_embed_vs_main_ui();

  // The controls layout used to work in Chrome without the hack,
  // but now behaves wrongly when the input bar is reduced to minimum height.
  // With the hack, it seems to work.
  // if (isFirefox || isSafari)
  controls_layout_hack_for_firefox_and_safari();
  load_theme();
  setup_dev_early();
  on_hash_change();

  $on($content, "input", message_changed);
  restore_content();
  message_changed();

  // enable keyboard shortcuts
  $on(document, "keydown", view_option);
  $on(document, "keyup", view_option);
  $on(document, "keydown", (ev) => dispatch_shortcut(ev, shortcuts.global));
  $on($content, "keydown", (ev) => dispatch_shortcut(ev, shortcuts.message));
  $on($content, "keydown", content_keydown);
  $on($room, "keypress", (ev) => dispatch_shortcut(ev, shortcuts.room));
  $on($id('filter_query'), "keypress", (ev) => dispatch_shortcut(ev, shortcuts.filter));
  $on($edit, "keydown", (ev) => dispatch_shortcut(ev, shortcuts.edit));

  $on($id("send"), "click", send);

  $on($id("add"), "click", () => set_controls("input_add"));
  $on($id("mod"), "click", () => set_controls("input_mod"));
  $on($id("view"), "click", () => set_controls("input_view"));
  $on($id("opt"), "click", () => set_controls("input_opt"));
  $on($id("audio"), "click", () => set_controls("input_audio"));

  $on($id("nav"), "click", nav_click);
  $on($id("pages"), "click", pages_click);
  $on($id("select"), "click", select_click);
  /* $on($id("scroll"), "click", () => set_top("top_scroll")); */
  $on($id("filter"), "click", () => set_top("top_filter"));
  $on($id("room_ops"), "click", () => set_top_left("top_left_room_ops"));

  // select functions
  $on($id("select_cancel"), "click", select_cancel);

  $on($id("mod_undo"), "click", undo);
  $on($id("mod_retry"), "click", retry);
  $on($id("mod_clear"), "click", clear_chat);
  $on($id("mod_archive"), "click", archive_chat);
  $on($id("mod_archive_2"), "click", archive_chat);
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
  $on($id("edit_close"), "click", edit_close_back);
  $on($id("edit_indent"), "click", edit_indent);
  $on($id("edit_dedent"), "click", edit_dedent);

  $on($id("view_theme"), "click", change_theme);
  $on($id("view_theme_bw"), "click", change_theme);
  $on($id("view_ids"), "click", view_ids);
  $on($id("view_images"), "click", view_images);
  $on($id("view_alt"), "click", view_alt);
  $on($id("view_image_size"), "click", view_image_size);
  $on($id("view_font_size"), "click", view_font_size);
  $on($id("view_source"), "click", view_source);
  $on($id("view_highlight"), "click", view_highlight);
  $on($id("view_details"), "click", view_details);
  $on($id("view_canvas"), "click", view_canvas);
  $on($id("view_toc"), "click", view_toc);
  $on($id("view_clean"), "click", view_clean);
  $on($id("view_columns"), "click", view_columns);
  $on($id("view_compact"), "click", view_compact);
  $on($id("view_history"), "click", view_history);
  $on($id("view_fullscreen"), "click", view_fullscreen);
  $on($id("view_items"), "change", view_items);
  $on($id("view_items"), "keyup", view_items);
  $on($id("view_advanced"), "click", view_advanced);
  $on($id("view_standard"), "click", view_standard);
  $on($id("view_cancel"), "click", () => set_controls());

  $on($id("opt_context"), "change", opt_context);
  $on($id("opt_lines"), "change", opt_lines);
  $on($id("opt_images"), "change", opt_images);
  $on($id("opt_temp"), "change", opt_temp);
  $on($id("opt_mission"), "change", opt_mission);
  $on($id("opt_cancel"), "click", () => set_controls());

  $on($id("nav_cancel"), "click", () => set_top_left());
  $on($id("pages_cancel"), "click", () => set_top_left());

  $on($id("dir_sort"), "click", dir_sort);

  // $on($id("scroll_home"), "click", (ev) => scroll_home_end(ev, 0));
  // $on($id("scroll_end"), "click", (ev) => scroll_home_end(ev, 1));
  $on($id("scroll_end_2"), "click", (ev) => scroll_home_end(ev, 2));
  // $on($id("scroll_pageup"), "click", (ev) => scroll_pages(ev, -1));
  // $on($id("scroll_pagedown"), "click", (ev) => scroll_pages(ev, 1));
  // $on($id("scroll_cancel"), "click", () => set_top());

  $on($id('filter_query'), "change", filter_changed);  // or on "input"
  $on($id("filter_2"), "click", () => set_top());

  if (iOS && navigator.standalone)
    $on(window, "scroll", iOS_reload_scroll);

  $on($id("room_ops_move"), "click", move_mode);
  $on($id("room_ops_copy"), "click", copy_mode);
  $on($id("room_ops_cancel"), "click", () => set_top_left());

  $on($id("audio_cancel"), "click", () => set_controls());

  $on($room, "change", () => set_room());
  $on(window, "hashchange", on_hash_change);
  $on(window, "message", handle_message);
  const dragControls = initDragControls();
  $on($id("resizer"), "mousedown", (ev) => !simple && dragControls(ev));
  $on($id("resizer"), "touchstart", (ev) => !simple && dragControls(ev));

  $on(window, "beforeprint", print_chat);

  $on(document, "fullscreenchange", fullscreenchange);

  $content.addEventListener('dragover', content_dragover);
  $content.addEventListener('dragleave', content_dragleave);
  $content.addEventListener('drop', content_drop);
  $content.addEventListener('paste', content_paste);

  if (isMobile)
    setup_view_option_long_press();

  $on($content, "click", hide_placeholder);

  notify_main();
  record_main();

  focus_content_on_pc();

  load_user_files();  // async

  beta_test();

  welcome();  // async

  /* This breaks scrolling in view_edit, etc, and I forget why I added it!
  $on(document, "touchmove", function(e) {
    e.preventDefault();
  }, { passive: false });
  */
}
