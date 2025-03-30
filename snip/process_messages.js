  // Combine messages from the same user
  // if message is hidden, i.e. an editing command, don't combine it
  if (!newMessage.classList.contains("hidden"))
    newMessage = combineMessages(newMessage, idClass);

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
        copyImages(paragraph, prevParagraph, id);
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
        copyImages(paragraph, prevParagraph, id);
      } else {
        copyContent(content, prevContent, id);
      }
      message.classList.add("hidden");
      message = null;
    }
  }

  return message;
}

function getLastVisibleMessageId() {
  let lastMessage = $messages.lastElementChild;
  while (lastMessage && lastMessage.classList.contains("hidden"))
    lastMessage = lastMessage.previousElementSibling;
  if (!lastMessage) {
    console.log("no last message found");
    return 0;
  }
  const moved = lastMessage.querySelectorAll(".moved:not(.hidden)");
  if (moved.length > 0) {
    const lastMoved = moved[moved.length - 1];
    console.log("last moved", lastMoved);
    return getMessageId(lastMoved);
  } else {
    console.log("last message", lastMessage);
    return getMessageId(lastMessage);
  }
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

function isNodeOnlyImages(node) {
  const hasImage = node.getElementsByTagName("img").length > 0;
  const hasText = Array.from(node.childNodes).some(
    (child) => child.nodeType === 3 && child.textContent.trim() !== ""
  );
  return hasImage && !hasText;
}

function copyContent(source, target, id) {
  const idClass = "m" + id;
  const span = document.createElement('span');
  span.classList.add(idClass);
  span.classList.add("moved");
  span.appendChild(document.createTextNode("\n"));
  addIdField(span, idClass);

  let el = source.firstChild;
  while (el) {
    span.appendChild(el.cloneNode(true));
    el = el.nextSibling;
  }

  target.appendChild(span);
}

function copyImages(source, target, id) {
  const idClass = "m" + id;
  const span = document.createElement('span');
  span.classList.add(idClass);
  span.classList.add("moved");
  addIdField(span, idClass);

  let el = source.firstChild;
  while (el) {
    if (el.classList.contains("image")) {
      const clone = el.cloneNode(true);
      span.appendChild(document.createTextNode(" "));
      span.appendChild(clone);
    }
    el = el.nextSibling;
  }

  target.appendChild(span);
}

function nodeIsMessage(node) {
  return node.nodeType === 1 && node.classList.contains("message");
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

function getAltText(img) {
  let alt = img.getAttribute("alt") || "";
  // strip off prefixed seed like #1234
  alt = alt.replace(/^#\d+\s*/, "");
  return alt;
}

function getPreviousVisibleMessage(element) {
  let prev = element.previousElementSibling;
  while (prev && prev.classList.contains("hidden"))
    prev = prev.previousElementSibling;
  return prev;
}

function find_message_id_tagged_children(element) {
  return Array.from(element.querySelectorAll('[class*="m"]')).filter(el =>
    /(?:^|\s)m(\d+)(?:\s|$)/.test(el.className)
  )
}

function reprocess_tagged_children($el) {
  console.log("reprocessing tagged children", $el);
  const tagged_children = find_message_id_tagged_children($el);
  for (const $child of tagged_children) {
    const id = getMessageId($child);
    const $main = $(`.message.m${id}:not(.removed)`);
    if (!$main)
      continue;
    console.log("  - unhiding", $main);
    $main.classList.remove("hidden");
    process_messages([$main]);
  }
}

    // check for any message IDs within the content,
    // unhide the corresponding main messages, and re-processes them in order
    reprocess_tagged_children($el);

function find_message_id_tagged_children(element) {
  return Array.from(element.querySelectorAll('[class*="m"]')).filter(el =>
    /(?:^|\s)m(\d+)(?:\s|$)/.test(el.className)
  )
}

function reprocess_tagged_children($el) {
  console.log("reprocessing tagged children", $el);
  const tagged_children = find_message_id_tagged_children($el);
  for (const $child of tagged_children) {
    const id = getMessageId($child);
    const $main = $(`.message.m${id}:not(.removed)`);
    if (!$main)
      continue;
    console.log("  - unhiding", $main);
    $main.classList.remove("hidden");
    process_messages([$main]);
  }
}
