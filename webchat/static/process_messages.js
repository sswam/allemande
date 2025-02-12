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
  return img.getAttribute("alt") || "";
}

function findMatchingImageMessage(message) {
  const user = message.getAttribute("user");
  const imgAlt = getAltText(message.querySelector("img"));

  for (let current = message.previousElementSibling; current; current = current.previousElementSibling) {
    if (!isNodeOnlyImages(current)) {
      continue;
    }
    if (current.getAttribute("user") !== user) {
      console.log("image message with different user", current);
      return null;
    }
    const currentImg = current.querySelector("img");
    if (currentImg) {
      if (getAltText(currentImg) === imgAlt) {
        return current;
      }
      console.log("image message with different alt text", current);
      return null;
    }
  }
  console.log("no matching image message found");
  return null;
}

function getOnlyChildParagraph(node) {
  const children = node.childNodes;
  if (children.length !== 1) {
    return null;
  }
  const child = children[0];
  if (child.nodeType === 1 && child.nodeName === "P") {
    return child;
  }
  return null;
}

function handleNewMessage(newMessage) {
  if (!newMessage.previousElementSibling) {
    return;
  }

  // Set title attribute for images
  const images = newMessage.querySelectorAll("img");
  for (const img of images) {
    if (!img.title && img.alt) {
      img.title = img.alt;
    }
  }

  const newContent = newMessage.querySelector(".content");
  const newParagraph = getOnlyChildParagraph(newContent);

  // Handle image-only messages
  if (newParagraph && isNodeOnlyImages(newParagraph)) {
    const matchingMessage = findMatchingImageMessage(newMessage);
    if (!matchingMessage) {
      return;
    }
    console.log("found matching", matchingMessage);
    const prevContent = matchingMessage.querySelector(".content");
    const prevParagraph = getOnlyChildParagraph(prevContent);
    if (prevParagraph) {
      moveImages(newParagraph, prevParagraph);
      newMessage.remove();
    }
    return;
  }

  // Handle regular messages
  const previousMessage = newMessage.previousElementSibling;
  if (!nodeIsMessage(previousMessage) ||
      previousMessage.getAttribute("user") !== newMessage.getAttribute("user")) {
    return;
  }

  const prevContent = previousMessage.querySelector(".content");
  moveContent(newContent, prevContent);
  newMessage.remove();
}

function observeMessages(mutations) {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (nodeIsMessage(node)) {
        handleNewMessage(node);
      }
    }
  }
}

function combineMessagesPlugin(container) {
  const observer = new MutationObserver(observeMessages);
  observer.observe(container, { childList: true, subtree: true });
  return observer;
}

combineMessagesPlugin(document);
