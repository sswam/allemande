on Linux with inotify or whatever any way to distinguish appending vs general editing?  when something is appended I can process just the extra lines, but when it is edited I need to reprocess the whole file (or from the edit point at least).
Please reply as concise as possible, with no boilerplate or unnecessary explanation.

You can use inotify with the IN_MODIFY and IN_APPEND flags:

1. IN_MODIFY: Triggered for any file modification.
2. IN_APPEND: Triggered specifically for append operations.

Use IN_APPEND to process only new lines.
Use IN_MODIFY to reprocess the whole file or from the last known position.

To implement:
1. Set up inotify watch with both flags.
2. In event handler, check event->mask.
3. Process accordingly based on the flag.

Note: Some editors may trigger IN_MODIFY even for appends.

