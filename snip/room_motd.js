/* Not ideal, as scripts could read it */

// message of the day --------------------------------------------------------

function motd(text) {
    const div = document.createElement('div');
    div.className = 'motd';
    div.textContent = text;
    div.style.cssText = 'position:fixed; top:var(--pad,1rem); right:var(--pad,1rem); cursor:pointer';
    $on(div, "click", () => div.remove();
    document.body.appendChild(div);
}

/* Optional suggestions:
- Could add color/bg/padding/border styles for visibility
- Consider transition for fade-out
- Maybe allow HTML content instead of just text
*/

