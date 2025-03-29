"use strict";
var inIframe = window.parent !== window.self;
const moveLabels = true;

const HIDE_CONTROLS_DELAY = 1000;

function isNodeOnlyImages(node) {
  const hasImage = node.getElementsByTagName("img").length > 0;
  const hasText = Array.from(node.childNodes).some(
    (child) => child.nodeType === 3 && child.textContent.trim() !== ""
  );
  return hasImage && !hasText;
}

function copyContent(source, target, idClass) {
  target.appendChild(document.createTextNode("\n"));
  let el = source.firstChild;
  while (el) {
    console.log(el);
    if (el.nodeType === 1)
      el.classList.add(idClass);
    target.appendChild(el.cloneNode(true));
    el = el.nextSibling;
  }
}

function copyImages(source, target, idClass) {
  let el = source.firstChild;
  while (el) {
    if (el.classList.contains("image")) {
      const clone = el.cloneNode(true);
      clone.classList.add(idClass);
      target.appendChild(document.createTextNode(" "));
      target.appendChild(clone);
    }
    el = el.nextSibling;
  }
}

function nodeIsMessage(node) {
  return node.nodeType === 1 && node.classList.contains("message");
}

function getAltText(img) {
  let alt = img.getAttribute("alt") || "";
  // strip off prefixed seed like #1234
  alt = alt.replace(/^#\d+\s*/, "");
  return alt;
}

function findMatchingImageMessage(message) {
  const user = message.getAttribute("user");
  const imgAlt = getAltText(message.querySelector("img"));

  for (
    let current = message.previousElementSibling;
    current;
    current = current.previousElementSibling
  ) {
    if (current.classList.contains("hidden"))
      continue;
    if (!isNodeOnlyImages(current))
      continue;
    if (current.getAttribute("user") !== user)
      return null;
    const currentImg = current.querySelector("img");
    if (currentImg) {
      if (getAltText(currentImg) === imgAlt)
        return current;
      return null;
    }
  }
  return null;
}

function getOnlyChildParagraph(node) {
  const children = node.childNodes;
  if (!children || children.length !== 1) {
    return null;
  }
  const child = children[0];
  if (child.nodeType === 1 && child.nodeName === "P") {
    return child;
  }
  return null;
}

function render_graphviz(node) {
  const dot = node.querySelectorAll("code.language-dot");
  for (const elem of dot) {
    const par = elem.parentElement;
    d3.select(par)
      .append("div")
      .classed("graphviz", true)
      .graphviz()
      .renderDot(elem.innerText);
  }
}

function render_mermaid(node) {
  const mermaidCode = node.querySelectorAll("code.language-mermaid");
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

function getMessageId(element) {
  let id;
  const match = element.className.match(/(?:^|\s)m(\d+)(?:\s|$)/);
  if (match) {
    id = parseInt(match[1]);
  } else {
    const prev = element.previousElementSibling;
    if (!prev) {
      id = 0;
    } else {
      id = getMessageId(prev) + 1;
    }
    element.classList.add("m" + id);
  }
  return id;
}

function getPreviousVisibleMessage(element) {
  let prev = element.previousElementSibling;
  while (prev && prev.classList.contains("hidden"))
    prev = prev.previousElementSibling;
  return prev;
}

function handleNewMessage(newMessage) {
  // if hidden, don't process
  if (newMessage.classList.contains("hidden"))
    return;

  // console.log("handling new message", newMessage);
  const newContent = newMessage.querySelector(".content");
  const newUser = newMessage.getAttribute("user");

  // Add message number as a class, like m123
  const id = getMessageId(newMessage);
  const idClass = "m" + id;

  notify_new_message({ user: newUser, content: newContent.innerHTML });

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

  // render graphviz diagrams
  render_graphviz(newContent);

  // render mermaid diagrams
  render_mermaid(newContent);

  // add language info to code blocks, script and styles on hover
  const codeBlocks = newContent.querySelectorAll(
    "code, script:not(hide):not([src]), style:not(hide)"
  );
  for (const codeBlock of codeBlocks) {
    decorateCodeBlock(codeBlock);
  }

  // Open details elements according to the view options
  for (const $details of newContent.querySelectorAll("details"))
    open_or_close_details($details);

  // Code highlighting according to the view options
  highlight_code(newMessage, view_options);

  // Combine messages from the same user
  newMessage = combineMessages(newMessage, idClass);

  // Move label inside first paragraph; dodgy hack because float is broken with break-after: avoid
  if (newMessage && moveLabels) {
    const label = newMessage.querySelector(".label");
    // console.log("trying to move label for message ID", id, "label", label);
    // console.log("new message", newMessage);
    if (label) {
      let p = newContent.querySelector(":scope > p");
      // console.log("first paragraph", p);
      let go_before_this = newMessage.querySelector(
        "pre, details, script, style"
      );
      let container =
        p && !(go_before_this && isPrecedingSibling(go_before_this, p))
          ? p
          : newContent;
      /*
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
      */
      container.insertBefore(label, container.firstChild);
    }
  }
}

function combineMessages(message) {
  const content = message.querySelector(".content");
  const user = message.getAttribute("user");
  const id = getMessageId(message);
  const idClass = "m" + id;

  const paragraph = getOnlyChildParagraph(content);

  // Move images from new message to previous message if they have
  // the same user and same generation prompt in the alt text
  if (paragraph && isNodeOnlyImages(paragraph)) {
    const matchingMessage = findMatchingImageMessage(message);
    if (matchingMessage) {
      // console.log("found matching", matchingMessage);
      const prevContent = matchingMessage.querySelector(".content");
      const prevParagraph = getOnlyChildParagraph(prevContent);
      if (prevParagraph) {
        copyImages(paragraph, prevParagraph, idClass);
        message.classList.add("hidden");
        message = null;
      }
    }
  }

  // Combine regular messages from the same user
  if (message) {
    const previousMessage = getPreviousVisibleMessage(message);
    if (
      previousMessage &&
      nodeIsMessage(previousMessage) &&
      previousMessage.getAttribute("user") === user
    ) {
      const prevContent = previousMessage.querySelector(".content");
      const prevParagraph = getOnlyChildParagraph(prevContent);
      // If images, combine them into the same paragraph
      if (
        paragraph &&
        isNodeOnlyImages(paragraph) &&
        prevParagraph &&
        isNodeOnlyImages(prevParagraph)
      ) {
        copyImages(paragraph, prevParagraph, idClass);
      } else {
        copyContent(content, prevContent, idClass);
      }
      message.classList.add("hidden");
      message = null;
    }
  }

  return message;
}

function isPrecedingSibling(node1, node2) {
  return (
    node1.compareDocumentPosition(node2) & Node.DOCUMENT_POSITION_FOLLOWING
  );
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
  if (
    codeBlock.nodeName === "STYLE" &&
    codeBlock.textContent.includes(".katex img")
  ) {
    return;
  }

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
    }
    if (inIframe) {
      // send text to parent window
      window.parent.postMessage({ type: "copy", text: text }, CHAT_URL);
    } else {
      // copy text to clipboard
      await navigator.clipboard.writeText(text);
    }
    flash(controls, "active");
  });

  // Add controls to wrapper
  parent.appendChild(controls);

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

function process_messages(new_content) {
  for (const newMessage of new_content) {
    handleNewMessage(newMessage);
  }
}

// history editing functions -------------------------------------------------

function findMessageIdTaggedChildren(element) {
  return Array.from(element.querySelectorAll('[class*="m"]')).filter(el =>
    /(?:^|\s)m(\d+)(?:\s|$)/.test(el.className)
  )
}

function reprocess_tagged_children($el) {
  const taggedChildren = findMessageIdTaggedChildren($el);
  for (const $child of taggedChildren) {
    const id = getMessageId($child);
    const $main = $(`.message.m${id}:not(.removed)`);
    if (!$main)
      continue;
    $main.classList.remove("hidden");
    process_messages([$main]);
  }
}

async function get_script_message_and_id() {
  const script = document.currentScript;
  console.log("script", script);
  const script_message = script.closest('.message');
  if (!script_message) {
    throw new Error("script not in message");
  }
  const script_message_id = getMessageId(script_message);
  await wait_for_whole_message(script_message);
  return { script, script_message, script_message_id };
}

async function remove2(messageId) {
  const idClass = `m${messageId}`;
  let message = null;
  // add class hidden to all matching elements
  for (const $el of $$(`.${idClass}`)) {
    $el.classList.add("hidden");
    $el.classList.add("removed");
    if (!$el.classList.contains("message"))
      continue;
    message = $el;
    // check for any message IDs within the content,
    // unhide the corresponding main messages, and re-processes them in order
    reprocess_tagged_children($el);
  }
  if (!message)
    console.error(`remove: message ${messageId} not found`);
  return message;
}

async function remove(messageId) {
  const { script, script_message, script_message_id } = await get_script_message_and_id();
  const message = await remove2(messageId);
  // remove the script element
  script.remove();
  // hide the message that contained the script if it's now empty
  if (script_message && !script_message.querySelector(".content").innerHTML.trim())
    script_message.classList.add("hidden");
  return message;
}

async function insert2(messageId, message) {
  const idClass = `m${messageId}`;
  const $el = $(`.message.${idClass}`);
  if (!$el) {
    console.error(`insert: message ${messageId} not found`);
    return;
  }
  // insert a placeholder with same ID before the message where it is
  const placeholder = document.createElement("div");
  placeholder.classList.add(idClass);
  placeholder.classList.add("hidden");
  placeholder.classList.add("placeholder");
  message.before(placeholder);
  // insert message before $el
  $el.before(message);
  return message;
}

async function insert(messageId) {
  const { script, script_message, script_message_id } = await get_script_message_and_id();
  const message = await insert2(messageId, script_message);
  // remove the script element
  script.remove();
  return message;
}

async function edit(messageId) {
  const { script, script_message, script_message_id } = await get_script_message_and_id();
  console.log("edit: script_message", script_message);
  // remove then insert
  const replaced = await remove2(messageId, true);
  if (!replaced)
    return;
  const message = await insert2(messageId, script_message);
  // we need to tag the message with the old message ID
  // using data-prev attribute
  console.log("edit: message", message);
  console.log("edit: message.dataset", message.dataset);
  message.dataset.prev = messageId;
  // mark the old message as edited
  replaced.classList.add("edited");
  // remove the script element
  script.remove();
  return message;
}
