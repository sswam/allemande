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

function moveContent(source, target) {
  target.appendChild(document.createTextNode("\n"));
  while (source.firstChild) {
    target.appendChild(source.firstChild);
  }
}

function moveImages(source, target) {
  while (source.firstChild) {
    if (source.firstChild.className === "image") {
      target.appendChild(document.createTextNode(" "));
      target.appendChild(source.firstChild);
    } else {
      source.removeChild(source.firstChild);
    }
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
    if (!isNodeOnlyImages(current)) {
      continue;
    }
    if (current.getAttribute("user") !== user) {
      // console.log("image message with different user", current);
      return null;
    }
    const currentImg = current.querySelector("img");
    if (currentImg) {
      if (getAltText(currentImg) === imgAlt) {
        return current;
      }
      // console.log("image message with different alt text", current);
      return null;
    }
  }
  // console.log("no matching image message found");
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
      });
  }
}

function handleNewMessage(newMessage) {
  // console.log("handling new message", newMessage);
  const newContent = newMessage.querySelector(".content");
  const newUser = newMessage.getAttribute("user");
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

  const newParagraph = getOnlyChildParagraph(newContent);

  // Move images from new message to previous message if they have
  // the same user and same generation prompt in the alt text
  if (newParagraph && isNodeOnlyImages(newParagraph)) {
    const matchingMessage = findMatchingImageMessage(newMessage);
    if (matchingMessage) {
      // console.log("found matching", matchingMessage);
      const prevContent = matchingMessage.querySelector(".content");
      const prevParagraph = getOnlyChildParagraph(prevContent);
      if (prevParagraph) {
        moveImages(newParagraph, prevParagraph);
        newMessage.remove();
        newMessage = null;
      }
    }
  }

  // Combine regular messages from the same user
  if (newMessage) {
    const previousMessage = newMessage.previousElementSibling;
    if (
      previousMessage &&
      nodeIsMessage(previousMessage) &&
      previousMessage.getAttribute("user") === newUser
    ) {
      const prevContent = previousMessage.querySelector(".content");
      const prevParagraph = getOnlyChildParagraph(prevContent);
      // If images, combine them into the same paragraph
      if (
        newParagraph &&
        isNodeOnlyImages(newParagraph) &&
        prevParagraph &&
        isNodeOnlyImages(prevParagraph)
      ) {
        moveImages(newParagraph, prevParagraph);
      } else {
        moveContent(newContent, prevContent);
      }
      newMessage.remove();
      newMessage = null;
    }
  }

  // Move label inside first paragraph; dodgy hack because float is broken with break-after: avoid
  if (newMessage && moveLabels) {
    const label = newMessage.querySelector(".label");
    if (label) {
      let p = newContent.querySelector(":scope > p");
      let go_before_this = newMessage.querySelector(
        "pre, details, script, style"
      );
      let container =
        p && !(go_before_this && isPrecedingSibling(go_before_this, p))
          ? p
          : newContent;
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
