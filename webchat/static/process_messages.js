"use strict";
var inIframe = window.parent !== window.self;
const moveLabels = true;

function isNodeOnlyImages(node) {
  const hasImage = node.getElementsByTagName('img').length > 0;
  const hasText = Array.from(node.childNodes).some(
    child => child.nodeType === 3 && child.textContent.trim() !== ''
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
    if (source.firstChild.nodeName === "IMG") {
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

  for (let current = message.previousElementSibling; current; current = current.previousElementSibling) {
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

function handleNewMessage(newMessage) {
  // console.log("handling new message", newMessage);
  const newContent = newMessage.querySelector(".content");
  const newUser = newMessage.getAttribute("user");
  notify_new_message({ user: newUser, content: newContent.innerHTML });

  // Set title attribute for images
  // and add a <div class="alt"> element for each image
  const images = newMessage.querySelectorAll("img");
  for (const img of images) {
    if (!img.title && img.alt) {
      // console.log("setting title", img.alt);
      img.title = img.alt;
    }
    const altDiv = document.createElement("div");
    altDiv.className = "alt";
    altDiv.textContent = "🖼️ " + img.alt;
    img.parentNode.insertBefore(altDiv, img.nextSibling);
  }

  if (newUser) {
    // add class="me" to messages from the current user
    if (newUser.toLowerCase() === user) {
      newMessage.classList.add("me");
    }

    // mark specialist messages
    const specialists = ["pixi", "illu", "sia", "sio", "summi", "summar", "pliny", "atla", "chaz", "morf", "brie"];  // TODO: read from config, extend list
    if (specialists.includes(newUser.toLowerCase())) {
      newMessage.classList.add("specialist");
    }

    // mark narrative messages
    const narrators = ["illy", "yoni", "coni", "poni", "boni", "bigi", "pigi", "nova"];  // TODO: read from config, extend list
    if (narrators.includes(newUser.toLowerCase())) {
      newMessage.classList.add("narrative");
    }

    // mark messages invoking or mentioning a specialist, match whole word case-insensitive

    const pattern = new RegExp(`\\b(${specialists.join("|")})\\b`, "i");
    if (newContent && pattern.test(newContent.textContent)) {
      newMessage.classList.add("invoke-specialist");
    }
  }

  // console.log(newMessage.outerHTML);

  // render graphviz diagrams
  render_graphviz(newContent);

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

  // add language info and a copy button to code blocks on hover
  const codeBlocks = newContent.querySelectorAll("pre code");
  for (const codeBlock of codeBlocks) {
    decorateCodeBlock(codeBlock);
  }

  // Combine regular messages from the same user
  if (newMessage) {
    const previousMessage = newMessage.previousElementSibling;
    if (previousMessage && nodeIsMessage(previousMessage) && previousMessage.getAttribute("user") === newMessage.getAttribute("user")) {
      const prevContent = previousMessage.querySelector(".content");
      const prevParagraph = getOnlyChildParagraph(prevContent);
      // If images, combine them into the same paragraph
      if (newParagraph && isNodeOnlyImages(newParagraph) && prevParagraph && isNodeOnlyImages(prevParagraph)) {
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
      const firstChild = newContent.firstChild;
      if (firstChild && firstChild.nodeName === "P") {
        firstChild.insertBefore(label, firstChild.firstChild);
      }
    }
  }
}

function decorateCodeBlock(codeBlock) {
  const lang = codeBlock.className.replace(/language-/, "");
  const pre = codeBlock.parentNode;

/*  // Create wrapper for the code block to help with positioning
  const wrapper = document.createElement('div');
  wrapper.style.position = 'relative';
  codeBlock.parentNode.insertBefore(wrapper, codeBlock);
  wrapper.appendChild(codeBlock);
*/

  // Create container for language label and copy button
  const controls = document.createElement('div');
  controls.className = 'code-controls';

  // Add language label if language is specified
  if (lang) {
    controls.textContent = lang;
  }

  // Create copy button
  const copyButton = document.createElement('button');
  copyButton.id = 'copy_button';
  copyButton.textContent = 'copy';
  controls.appendChild(copyButton);

  // Add click handler for copy button
  copyButton.addEventListener('click', async () => {
    if (inIframe) {
      // send text to parent window
      window.parent.postMessage({"type": "copy", "text": codeBlock.textContent}, CHAT_URL);
    } else {
      // copy text to clipboard
      await navigator.clipboard.writeText(codeBlock.textContent);
    }
    flash(copyButton, 'active');
  });

  // Add controls to wrapper
  pre.appendChild(controls);

  // Show/hide controls on hover
  pre.addEventListener('mouseenter', () => {
    controls.classList.add('show-flex');
    // controls.style.display = 'flex';
  });

  pre.addEventListener('mouseleave', (e) => {
    // Check if the mouse is not over the controls
    if (!controls.contains(e.relatedTarget)) {
      controls.classList.remove('show-flex');
      // controls.style.display = 'none';
    }
  });

  // Add additional listener to controls to prevent hiding when hovering over them
  controls.addEventListener('mouseenter', () => {
    controls.classList.add('show-flex');
    // controls.style.display = 'flex';
  });
}

function process_messages(new_content) {
  for (const newMessage of new_content) {
    handleNewMessage(newMessage);
  }
}
