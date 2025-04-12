// mobile keyboards ----------------------------------------------------------

function visual_viewport_resized() {
  const height = `${window.visualViewport.height}px`;
//  document.documentElement.style.height = height;
  document.body.style.height = height;

  if (window.scrollY < 0)
    window.scrollTo(0, 0);
}
function account_for_chuckleheaded_mobile_keyboards() {
  $on(window.visualViewport, "resize", visual_viewport_resized);
  visual_viewport_resized();
}

  // account_for_chuckleheaded_mobile_keyboards();
