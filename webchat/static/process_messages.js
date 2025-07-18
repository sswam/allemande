var inIframe = window.parent !== window.self;
const moveLabels = true;
const room = await $import("chat:room");

const HIDE_CONTROLS_DELAY = 1000;

async function render_math(node) {
  const codes = node.querySelectorAll("code.language-latex");
  if (codes.length === 0)
    return;
  await ensure_katex_scripts();
  // TODO try / catch on each element, for protection against bad TeX?
  for (const elem of codes) {
    const par = elem.parentElement;
    const displayMode = par.tagName === "PRE";
    const appendAfter = displayMode ? par : elem;
    const rendered = document.createElement('span');
    katex.render(elem.innerText, rendered, {
      throwOnError: false,
      displayMode: displayMode,
    });
    while (rendered.lastChild) {
      appendAfter.after(rendered.lastChild);
    }
  }
}

async function render_graphviz(node) {
  const codes = node.querySelectorAll("code.language-dot");
  if (codes.length === 0)
    return;
  await ensure_graphviz_scripts();
  for (const elem of codes) {
    const par = elem.parentElement;
    d3.select(par)
      .append("div")
      .classed("graphviz", true)
      .graphviz({useWorker: false})
      .renderDot(elem.innerText);
  }
}

async function render_mermaid(node) {
  const mermaidCode = node.querySelectorAll("code.language-mermaid");
  if (mermaidCode.length === 0)
    return;
  await ensure_mermaid_scripts();
  for (const elem of mermaidCode) {
    const par = elem.parentElement;
    const id = `mermaid-${Date.now()}`;
    mermaid.render(id, elem.innerText)
      .then(({ svg }) => {
        const div = document.createElement("div");
        div.className = "mermaid";
        div.innerHTML = svg;
        par.appendChild(div);
        const svgElement = div.querySelector('svg');
        svgElement.style.width = svgElement.style.maxWidth;
      });
  }
}

async function render_cards(node) {
  for (const el of node.querySelectorAll("card")) {
    const path = el.getAttribute("path");
    if (!path)
      continue;
    const card = await loadProfile(path);
    el.replaceWith(card);
  }
}

async function ensure_katex_scripts() {
  await Promise.all([
    $style("style_katex", `https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css`),
    $script("script_katex", `https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js`),
  ]);
}

async function ensure_graphviz_scripts() {
  await Promise.all([
    await $script("script_d3", `${ALLYCHAT_CHAT_URL}/d3.min.js`),
    await $script("script_graphviz_wasm", `${ALLYCHAT_CHAT_URL}/wasm.min.js`),
  ]);
  await $script("script_d3_grapviz", `${ALLYCHAT_CHAT_URL}/d3-graphviz.min.js`);
}

async function ensure_mermaid_scripts() {
  await $script("script_mermaid", `${ALLYCHAT_CHAT_URL}/mermaid.min.js`);
}

async function ensurePreviousMessagesProcessed(element) {
  let id = getMessageId(element);
  if (id !== null)
    return [id, true];
  const prev = element.previousElementSibling;
  if (!prev) {
    id = 0;
  } else {
    id = await processMessage(prev) + 1;
  }
  element.classList.add("m" + id);
  element.id = "m" + id;
  return [id, false];
}

function getMessageId(element) {
  let id = null;
  const match = element.className.match(/(?:^|\s)m(\d+)(?:\s|$)/);
  if (match)
    id = parseInt(match[1]);
  return id;
}

export async function processMessage(newMessage) {
  // Add message number as a class, like m123
  const [id, processed] = await ensurePreviousMessagesProcessed(newMessage);
  if (processed)
    return id;

  // const idClass = "m" + id;

  // if hidden, don't process
  if (newMessage.classList.contains("hidden"))
    return;

  // console.log("handling new message", newMessage);
  const newContent = newMessage.querySelector(".content");
  const newUser = newMessage.getAttribute("user");

  // Remove newline at start of paragraph, pre or code
  // Maybe not needed now? We'll see...
  /*
  for (const node of newContent.querySelectorAll("p, pre, code")) {
    if (node.firstChild && node.firstChild.nodeType === 3) {
      const text = node.firstChild.textContent;
      if (text === "\n" || text === "\r\n") {
        node.firstChild.remove();
      } else if (text.startsWith("\n")) {
        node.firstChild.textContent = node.firstChild.textContent.substring(1);
      } else if (text.startsWith("\r\n")) {
        node.firstChild.textContent = node.firstChild.textContent.substring(2);
      }
    }
  }
  */

  // Set title attribute for images
  // and add a <div class="alt"> element for each image
  const images = newMessage.querySelectorAll("img");
  for (const img of images) {
    if (!img.title && img.alt) {
      // console.log("setting title", img.alt);
      img.title = img.alt;
    }
    const wrapper = img.closest(".image, .embed");
    if (!(wrapper && wrapper.querySelector(".alt"))) {
      const parent = img.parentNode;
      const next = img.nextSibling;
      const wrapDiv = document.createElement("div");
      const altDiv = document.createElement("div");
      wrapDiv.className = "image";
      altDiv.className = "alt";
      //      altDiv.textContent = "🖼️ " + img.al;
      altDiv.textContent = img.alt;
      wrapDiv.appendChild(img);
      wrapDiv.appendChild(altDiv);
      parent.insertBefore(wrapDiv, next);
    }
  }

  if (newUser) {
    // add class="me" to messages from the current user
    if (newUser.toLowerCase() === user) {
      newMessage.classList.add("me");
    }

    // hide system messages
    if (newUser.toLowerCase() === "system") {
      newMessage.classList.add("hidden");
    }

    const summarisers = ["summi", "summar", "sia", "sio"]; // TODO: read from config, extend list

    // mark specialist messages
    const specialists = [
      "pixi",
      "illu",
      "gema",
      "xilu",
      "pliny",
      "atla",
      "chaz",
      "morf",
      "brie",
    ]; // TODO: read from config, extend list
    if (specialists.includes(newUser.toLowerCase())) {
      newMessage.classList.add("specialist");
    }

    // mark narrative messages
    const narrators = [
      "illy",
      "hily",
      "yoni",
      "coni",
      "poni",
      "boni",
      "bigi",
      "pigi",
      "dily",
      "wili",
      "nova",
    ]; // TODO: read from config, extend list
    if (narrators.includes(newUser.toLowerCase())) {
      newMessage.classList.add("narrative");
    }

    // mark messages invoking or mentioning a specialist, match whole word case-insensitive

    const pattern = new RegExp(`\\b(${specialists.join("|")})\\b`, "i");
    if (
      newContent &&
      pattern.test(newContent.textContent) &&
      !summarisers.includes(newUser.toLowerCase())
    ) {
      newMessage.classList.add("invoke-specialist");
    }
  }

  // console.log(newMessage.outerHTML);

  // render TeX math
  await render_math(newContent);

  // render graphviz diagrams
  await render_graphviz(newContent);

  // render mermaid diagrams
  await render_mermaid(newContent);

  // render profile cards
  render_cards(newContent);  // in background

  // add language info to code blocks, script and styles on hover
  const codeBlocks = newContent.querySelectorAll(
    "code, script:not(hide):not([src]), style:not(hide)"
  );
  for (const codeBlock of codeBlocks) {
    decorateCodeBlock(codeBlock);
  }

  // Open details elements according to the view options
  for (const $details of newContent.querySelectorAll("details"))
    room.open_or_close_details($details);

  // Code highlighting according to the view options
  await highlight_code(newMessage, room.view_options);

  // Processing editing commands
  await process_editing_commands(newMessage);

  // Move label inside first paragraph; dodgy hack because float is broken with break-after: avoid
  if (newMessage && moveLabels) {
    const label = newMessage.querySelector(".label");
    // console.log("trying to move label for message ID", id, "label", label);
    // console.log("new message", newMessage);
    if (label) {
      let p = newContent.querySelector(":scope > p");
      // console.log("first paragraph", p);
      let go_before_this = newMessage.querySelector(
        "pre, details, script:not([src]), style, ol, ul, blockquote, h1, h2, h3, h4, h5, h6"
      );
      let container;
      if (p && !(go_before_this && isPrecedingNode(go_before_this, p))) {
        container = p;
      } else {
        label.style.float = "left";
//        label.style.paddingRight = "1em";
        container = newContent;
      }
      container.insertBefore(label, container.firstChild);

      if (user.toLowerCase() === "gimg") {
        console.log(
          "moving label",
          label,
          "before",
          go_before_this,
          "in",
          container,
          "for",
          user
        );
      }
      container.insertBefore(label, container.firstChild);
    }
  }

  // Add ID labels which can be shown, div class=id
  const idDiv = document.createElement("div");
  idDiv.className = "id";
  idDiv.textContent = id;
  newMessage.appendChild(idDiv);

  // Prepend a checkbox for selecting it
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.className = "select";
  checkbox.id = "s" + id;
  newMessage.prepend(checkbox);

  // ID of last visible mesage in chat, for undo
  const lastMessageId = getLastVisibleMessageId();
  // console.log("last visible message ID", lastMessageId);

  // notify parent window of new message
  room.notify_new_message({ user: newUser, content: newContent.innerHTML, lastMessageId });

  return id;
}

function getLastVisibleMessageId() {
  const $messages = $("div.messages");
  let lastMessage = $messages.lastElementChild;
  while (lastMessage && lastMessage.classList.contains("hidden"))
    lastMessage = lastMessage.previousElementSibling;
  return lastMessage ? getMessageId(lastMessage) : null;
}

let hideTimer;
let controls_visible;

function showHideControls(controls, show) {
  // console.log("showHideControls", show, controls);
  if (hideTimer) {
    clearTimeout(hideTimer);
    hideTimer = null;
  }

  if (show) {
    if (controls_visible) {
      controls_visible.classList.remove("show-flex");
    }
    controls.classList.add("show-flex");
    controls_visible = controls;
  } else {
    hideTimer = setTimeout(function () {
      controls.classList.remove("show-flex");
      hideTimer = null;
    }, HIDE_CONTROLS_DELAY);
  }
}

function decorateCodeBlock(codeBlock) {
  /*
  if (
    codeBlock.nodeName === "STYLE" &&
    codeBlock.textContent.includes(".katex img")
  ) {
    return;
  }
  */

  // Add title click to copy
  codeBlock.title = "click to copy";

  let lang = (
    codeBlock.className
      .split(" ")
      .find((className) => className.startsWith("language-")) || ""
  ).replace("language-", "");

  const parent = codeBlock.parentNode;

  const parentIsPre = parent.nodeName === "PRE";

  if (codeBlock.nodeName === "SCRIPT") {
    lang = "javascript";
  } else if (codeBlock.nodeName === "STYLE") {
    lang = "css";
  }

  /*  // Create wrapper for the code block to help with positioning
  const wrapper = document.createElement('div');
  wrapper.style.position = 'relative';
  codeBlock.parentNode.insertBefore(wrapper, codeBlock);
  wrapper.appendChild(codeBlock);
*/

  // Create container for language label ~~and copy button~~
  const controls = document.createElement("div");
  controls.className = "code-controls";

  // Add language label if language is specified
  if (lang) {
    const div = document.createElement("div");
    div.className = "language";
    div.textContent = lang;
    controls.appendChild(div);
  }

  /* TODO clean up */

  /*
  // Create copy button
  const copyButton = document.createElement("button");
  copyButton.id = "copy_button";
  copyButton.textContent = "copy";
  controls.appendChild(copyButton);
  */

  // Add click handler for ~~copy button~~ code block
  //  copyButton.addEventListener("click", async () => {
  codeBlock.addEventListener("click", async () => {
    let text = codeBlock.textContent.trim();
    if (parentIsPre) {
      text = text.replace(/\n*$/, "\n");
      // if no lang, probably an image prompt; quote it
      if (!lang)
        text = "```\n" + text + "```\n";
    }
    if (inIframe) {
      // send text to parent window
      window.parent.postMessage({ type: "copy", text: text }, ALLYCHAT_CHAT_URL);
    } else {
      // copy text to clipboard
      await navigator.clipboard.writeText(text);
    }
    room.flash(controls, "active");
  });

  // Add controls to wrapper
  parent.appendChild(controls);

  /* TODO would be better to handle events at the top level, without duplicate handlers */

  // Show controls on hover
  codeBlock.addEventListener("mouseenter", function () {
    showHideControls(controls, true);
  });

  // Only hide when leave the parent, after a delay
  parent.addEventListener("mouseleave", function () {
    showHideControls(controls, false);
  });

  // Add additional listener to controls
  controls.addEventListener("mouseenter", function () {
    showHideControls(controls, true);
  });

  controls.addEventListener("mouseleave", function () {
    showHideControls(controls, false);
  });
}

export async function process_messages(new_content) {
  for (const newMessage of new_content) {
    await processMessage(newMessage);
  }
}

// history editing functions -------------------------------------------------

function remove(messageId, edit = false) {
  // console.log("removing message", messageId);
  const idClass = `m${messageId}`;
  let message = null;
  // add class hidden to all matching elements
  for (const $el of $$(`.${idClass}`)) {
    $el.classList.add("hidden");
    $el.classList.add("removed");
    if (!$el.classList.contains("message"))
      continue;
    message = $el;
  }
  if (!message) {
    console.error(`remove: message ${messageId} not found`);
    return;
  }
  if (edit) {
    // mark the message as edited
    // console.log("marking message as edited", message);
    message.classList.add("edited");
  }
  return message;
}

function insert(targetId, message) {
  // console.log("inserting message", message, "before", targetId);
  const targetIdClass = `m${targetId}`;
  const $target = $(`.message.${targetIdClass}`);
  if (!$target) {
    console.error(`insert: message ${targetIdClass} not found`);
    return;
  }
  // insert a placeholder with same ID before the message where it is
  const messageId = getMessageId(message);
  const idClass = `m${messageId}`;
  const placeholder = document.createElement("div");
  placeholder.classList.add(idClass);
  placeholder.classList.add("hidden");
  placeholder.classList.add("placeholder");
  message.before(placeholder);
  // insert message before $target
  $target.before(message);
  return message;
}

function get_message_meta(message) {
  return message.getElementsByTagName('ac');
}

function message_is_empty(message) {
    const content = message.querySelector('.content');
    const label = content.querySelector('.label');
    const hasNonLabelNonPContent = content.querySelector(':not(.label):not(p)');
    const contentText = content.textContent.trim();
    const labelText = label && label.textContent.trim();

    let empty;

    if (hasNonLabelNonPContent)
      empty = false;
    else if (!label)
      empty = contentText === '';
    else
      empty = contentText === labelText;

    return empty;
}

async function process_editing_commands(message) {
  const metas = get_message_meta(message);
  // if (metas.length > 0) {
  //   console.log("process_editing_commands: message", message.outerHTML);
  //   console.log("metas", metas);
  // }
  for (const meta of metas) {
    const remove_ids = meta.getAttribute("rm");
    const insert_id = meta.getAttribute("insert");
    const edit_id = meta.getAttribute("edit");
    meta.removeAttribute("rm");
    meta.removeAttribute("insert");
    meta.removeAttribute("edit");

    // if no attributes remain on the tag, remove the meta tag
    if (!meta.hasAttributes())
      meta.remove();

    // if the message content is now empty, aside from the label, hide the message
    if (message_is_empty(message)) {
      message.classList.add('hidden');
    }

    if (remove_ids) {
      for (const id of remove_ids.split(" "))
        remove(id);
    }

    if (edit_id)
      remove(edit_id, true);

    const point = insert_id || edit_id;
    if (point) {
      await insert(point, message);
      message.dataset.prev = point;
    }
  }
}
