
function stem_ext(filename) {
	const match = filename.match(/^(.+?)(?:\.([^.]+))?$/);
	return [match[1], match[2] || ''];
}

function av_element_html(tag, stem, url) {
	const $el = $create(tag);
	$el.ariaLabel = stem;
	$el.src = url;
	$el.controls = true;
	return $el.outerHTML;
}

	if (medium === 'image') {
		// insert the image into the message box as markdown
		$content.value += `![${stem}](${url})`;
	} else if (medium === 'audio') {
		// insert the audio into the message box as an audio element
		$content.value += av_element_html("audio", stem, url);
	} else if (medium === 'video') {
		// insert the video into the message box as a video element
		$content.value += av_element_html("video", stem, url);
	} else {
		// insert the URL into the message box as a markdown link
		$content.value += `[${stem}](${url})`;
	}


function edit_paste(ev) {
  if (ev.shiftKey || type != "file")
    return;
  let text = ev.clipboardData.getData('text');
  if (editor_file.endsWith(".yml")) {
    text = text.replace(/^/gm, "  ");
    document.execCommand('insertText', false, text);
  } else {
    return;
  }
  ev.preventDefault();
}

  $on($edit, "paste", edit_paste);
