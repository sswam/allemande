

class LineReader:
    """Read input a line at a time."""

    def __init__(self, get: Get, rstrip=True):
        self.get = get
        self.buffer = ""
        self.rstrip = rstrip

    def get(**kwargs) -> str | None:
        """Get a line."""
        if self.buffer is None:
            return None

        while "\n" not in self.buffer:
            chunk = self.get(**kwargs)

            eof = chunk is None

            if eof:
                line = self.buffer
                self.buffer = None
                self.get = None
                if self.rstrip:
                    line = line.rstrip("\r\n")
                return line

            self.buffer += chunk

        line, self.buffer = self.buffer.split("\n", 1)

        if self.rstrip:
            line = line.rstrip("\r\n")
        else:
            line += "\n"

        return line


def input(get: Get, **kwargs) -> Get:
    """Get a line from a chunky get."""
    return LineReader(get, **kwargs).get


def each(get: Get, **kwargs) -> str:
    """A generator that yields chunks from get."""
    while True:
        line = get(**kwargs)
        if line is None:
            break
        yield line



def lines(get: Get, **kwargs) -> str:
    """A generator that yields lines from a chunky get."""
    return each(line(get, **kwargs), **kwargs)


def whole(get: Get, **kwargs) -> str:
    """Get all input from get."""
    return "".join(each(get, **kwargs))


# TODO maybe passing flush through is important to support.

# TODO async functions; arguably we should always use async.
#      Not using async is an optimization.
#      But I can't handle changing this to async while I'm making other changes.

# TODO streaming CSVReader, JSONLReader, etc.

