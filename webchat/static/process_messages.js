"use strict";

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
  const newContent = newMessage.querySelector(".content");
  const newUser = newMessage.getAttribute("user");
  notify_new_message({ user: newUser, content: newContent.innerHTML });

  // Set title attribute for images
  // and add a <div class="alt"> element for each image
  const images = newMessage.querySelectorAll("img");
  for (const img of images) {
    if (!img.title && img.alt) {
      img.title = img.alt;
    }
    const altDiv = document.createElement("div");
    altDiv.className = "alt";
    altDiv.textContent = "🖼️ " + img.alt;
    img.parentNode.insertBefore(altDiv, img.nextSibling);
  }

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

  // Combine regular messages from the same user
  if (newMessage) {
    const previousMessage = newMessage.previousElementSibling;
    if (previousMessage && nodeIsMessage(previousMessage) && previousMessage.getAttribute("user") === newMessage.getAttribute("user")) {
      const prevContent = previousMessage.querySelector(".content");
      moveContent(newContent, prevContent);
      newMessage.remove();
    }
  }
}

function process_messages(mutations) {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (nodeIsMessage(node)) {
        handleNewMessage(node);
      }
    }
  }
}
