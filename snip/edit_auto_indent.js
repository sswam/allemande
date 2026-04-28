function edit_auto_indent(ev) {
  ev.preventDefault();

  const textarea = ev.target;
  const { value, selectionStart, selectionEnd } = textarea;

  // Get the start of the selection (selected text will be replaced by textarea_insert)
  const start = Math.min(selectionStart, selectionEnd);

  // Get the text before the cursor/selection-start to determine current line's indent
  const textBefore = value.substring(0, start);

  // Find the beginning of the current line
  const lineStart = textBefore.lastIndexOf('\n') + 1;
  const currentLine = textBefore.substring(lineStart);

  // Extract leading whitespace (spaces or tabs) from the current line
  const indentMatch = currentLine.match(/^([ \t]*)/);
  const indent = indentMatch ? indentMatch[1] : '';

  // Insert newline + same indent (textarea_insert handles replacing any selection)
  textarea_insert(textarea, '\n' + indent);
}
