The syncnode tool is intended to sync changes to folders of files across a network of systems.

The service talks HTTP, with some DAV extensions.

The service accepts connections on address/ports (--listen or -l, optional),
and makes outgoing connections to other host/s (--connect or -c, optional).
The service does not do SSL or auth itself, they are handled by nginx or similar.
So we need a --proxy -p option for outgoing connections, and we may want to look at X-Forwarded-For and X-Forwarded-User on incoming connections.

For incoming connections, SSL and auth are handled by an nginx reverse proxy or similar. For outgoing connections, the service can be its own SSL client.

It also watches directories (recursively) for changes using inotify or similar.
Linux is the intended platform, but portability wouldn't hurt.

The command-line arguments are directories to watch, with aliases assigned to
them, like alias:/path/to/dir, e.g.:  chatroom:/var/spool/chatroom

The nodes are peers, i.e. the protocol is symmetrical.
The protocol is based on HTTP.

A node may request to follow a directory with GET alias
The response is a TSV listing of all files under that directory, with their mtimes in UNIX timestamp format with nanoseconds.

A node may cancel following with DELETE alias
The response has an empty body.

A node may request a file with GET /alias/path/to/file
The response has an X-Timestamp header, the UNIX timestamp with nanoseconds, and the full contents of the file.

When a watched file changes, or a new file is seen, the node sends the file to all followers, using PUT /alias/path/to/file
including X-Timestamp and the full contents of the file.

We will improve efficieny with POST (for append) and PATCH later, also MOVE and COPY.

While the node listens to many things at once, it only performs one action at a time, to avoid race conditions.

The node must also accept incoming PUT requests and update its local files accordingly.

When a file is DELETED, we send DELETE requests to followers; and when we
receive a DELETE request, we delete the file in question (or return a 404).

I propose that we implement this in Go.
