async function print_and_go_back() {
  let $body = document.body;
  // hide the page on screen
  $body.classList.add("print");
  // wait for an event
  $on(window, "afterprint", () => window.history.back());
  // print the page
  window.print();
}

function setup_printing() {
  // check for ?snapshot=1 in URL, properly by parsing the query string
  let snapshot = false;
  const url = new URL(location.href);
  if (url.searchParams.has("snapshot")) {
    snapshot = url.searchParams.get("snapshot") && true;
  }

  // check for #print hash
  if (snapshot && location.hash === "#print")
    $on(window, "load", print_and_go_back);
}

setup_printing();
