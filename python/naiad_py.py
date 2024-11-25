#!/usr/bin/env python3

""" A simple notebook kernel for Python. """

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import ast
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr, contextmanager
import logging
import traceback
from collections import defaultdict
from types import ModuleType
import argparse
from urllib.parse import urlparse
import signal
import threading


logger = logging.getLogger(__name__)

__version__ = "0.1.2"

do_auth = False

notebooks: dict[str, dict] = defaultdict(dict)


def evaluate_code(code: str, namespace: dict) -> tuple[str | None, str, str, str | None]:
    """Evaluate code, handling a mix of statements and expressions.
    Returns tuple of (result, stdout, stderr, error)."""
    stdout = StringIO()
    stderr = StringIO()

    try:
        tree = ast.parse(code)
        if not tree.body:
            return None, "", "", None

        statements, result = None, None

        # Check if last node is an expression
        last_expr = None
        if isinstance(tree.body[-1], ast.Expr):
            last_expr = tree.body.pop().value
        statements = tree.body

        # Execute statements
        with redirect_stdout(stdout), redirect_stderr(stderr):
            if statements:
                exec_code = compile(ast.Module(body=statements, type_ignores=[]), "<string>", "exec")
                exec(exec_code, namespace)
            if last_expr:
                eval_code = compile(ast.Expression(body=last_expr), "<string>", "eval")
                result = eval(eval_code, namespace)

        return format_result(result), stdout.getvalue(), stderr.getvalue(), None

    except Exception as e:
        stack = traceback.extract_tb(e.__traceback__)
        stack = stack[1:]  # Remove last two frames (exec and <string>)
        traceback_str = "".join(traceback.format_list(stack)) + traceback.format_exception_only(type(e), e)[-1]
        return None, stdout.getvalue(), stderr.getvalue(), traceback_str


def format_result(value):
    """Try to return the result in the JSON, or use repr."""
    if value is None:
        return None
    try:
        json.dumps(value)
        return value
    except Exception:
        return repr(value)


class KernelHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests to the kernel."""

    def __init__(self, *args, **kwargs):
        logger.debug("initializing kernel handler")
        super().__init__(*args, **kwargs)

    def do_POST(self):
        """Handle POST requests."""
        # Get the notebook module
        notebook = self.path.strip("/")
        logger.debug("request: %s", notebook)

        namespace = notebooks[notebook]

        content_length = int(self.headers["Content-Length"])
        code = self.rfile.read(content_length).decode()

        if do_auth and self.headers.get("X-API-Key") != "your-secret-key":
            self.send_error(403)
            return

        result, stdout, stderr, exception = evaluate_code(code, namespace)
        response = {"result": result, "stdout": stdout, "stderr": stderr, "error": exception}

        logger.debug("response: %s", response)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        json_response = json.dumps(response, indent="\t") + "\n"
        self.wfile.write(json_response.encode())

@contextmanager
def run_server_in_thread(server):
    server_thread = threading.Thread(target=server.serve_forever)
    try:
        server_thread.start()
        yield server
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()

def signal_handler(signum, _frame):
    logger.info("Received signal, shutting down server")
    raise SystemExit(0)

def run_server(bind_addr):
    host, port = bind_addr

    server = HTTPServer(bind_addr, KernelHandler)
    logging.info(f"Starting server on {host}:{port}")

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    with run_server_in_thread(server):
        while True:
            signal.pause()

def run_client(args):
    # Implement client functionality here
    logging.info(f"Running client with args: {args}")
    pass


def parse_bind_address(bind_string, default_host='', default_port=None):
    """
    Parse a bind address string in formats like:
        '127.0.0.1:8080'
        'localhost:8000'
        ':8080'
        '192.168.1.10'
    Returns tuple of (host, port)
    """
    # Add // prefix if not present for proper URL parsing
    if not bind_string.startswith('//'):
        bind_string = '//' + bind_string

    result = urlparse(bind_string)
    host = result.hostname or default_host
    port = result.port or default_port

    return (host, port)


def parse_bind(bind_string):
    """Parse the bind address, with default host and port."""
    return parse_bind_address(bind_string, default_host='127.0.0.1', default_port=3541)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP Server/Client Application")

    # Logging options
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    log_group.add_argument("-v", "--verbose", action="store_true", help="Enable info logging")

    # Bind address option
    parser.add_argument("-b", "--bind", type=parse_bind, default=("127.0.0.1", 3541), help="Bind address and/or port")

    # Client mode option
    parser.add_argument("-s", "--server", action="store_true", help="Run server")

    # Additional arguments for client
    parser.add_argument("args", nargs="*", help="Additional arguments for client mode")

    args = parser.parse_args()

    # Set up logging
    if args.debug:
        log_level = logging.DEBUG
    elif args.verbose:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Run either client or server
    if args.server:
        run_server(args.bind)
    else:
        run_client(args.args)
