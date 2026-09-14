function mouse_over(e) {
  return; // XXX disabled for the moment
  if (e.target.contains(e.relatedTarget)) {
    // not a true enter / leave
    return;
  }

  if (!e.target.classList.contains("message")) {
    return;
  }

  console.log("mouse_over", e.target, e.relatedTarget);

  // check if over a message, and show message menu
  // const message = event.target.closest(".message");
  const message = e.target;
  if ($message_with_menu && message !== $message_with_menu) {
    hide_message_menu();
  }
  if (message && message !== $message_with_menu) {
    show_message_menu(message);
  }
}


function mouse_out(e) {
  return mouse_over(e); // for current needs, same handler is used
}


  $on($body, "mouseover", mouse_over);
  $on($body, "mouseout", mouse_out);
