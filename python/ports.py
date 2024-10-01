""" Allemande ports API, client library. """

import os
import time
from pathlib import Path
import logging
import asyncio

import yaml
from watchfiles import awatch, Change

__version__ = "0.1.1"

logger = logging.getLogger(__name__)


def get_default_port_name(server):
    """ Get the default port for a server. """
    user_id = os.environ["USER"]
    default_ports_dir = Path(os.environ["ALLEMANDE_PORTS"])/server
    #default_port_id = f'{user_id}-{os.getpid()}'   # TODO?
    default_port_id = f'{user_id}'
    default_port = str(default_ports_dir/default_port_id)
    return default_port


class PortClient:
    """ Client for making requests to the core server. """
    def __init__(self, port):
        self.port = Path(port)
        self.req_id = 0

    async def prepare_request(self, config=None):
        """ Make a request to the core server. """
        prep = self.port/"prep"
        req = prep/f"req-{self.req_id:06d}"
        self.req_id += 1

        # create the request directory, needs to be group writable
        umask = os.umask(0o007)
        try:
            req.mkdir(parents=True, exist_ok=True, mode=0o770)
        finally:
            os.umask(umask)

        if config:
            req_config = req/"config.yaml"
            # we could do this as async IO, seems unnecessary
            req_config.write_text(yaml.dump(config), encoding="utf-8")
        return req

    async def send_request(self, req):
        """ Send a request to the core server. """
        todo = self.port/"todo"
        # we could do this as async IO, seems unnecessary
        req.rename(todo/req.name)

    async def wait_for_response(self, req):
        """ Wait for a response from the core server. """
        done = self.port/"done"
        error = self.port/"error"

        async for changes in awatch(done, error, recursive=False):
            for change_type, path in changes:
                if change_type == Change.added:
                    resp = Path(path)
                    if resp.is_dir() and resp.name == req.name:
                        status = resp.parent.name
                        return resp, status

        raise RuntimeError("no response")  # TODO better error handling

    async def response_error(self, resp, raise_exception=True):
        """ Show the logs from a failed request. """
        log = resp/"log.txt"
        if log.exists():
            # we could do this as async IO, seems unnecessary
            log_text = log.read_text(encoding="utf-8")
            logger.error("request failed: %s", log_text)
            if raise_exception:
                raise RuntimeError(f"request failed: {log_text}")
                # TODO we should probably raise a more specific exception

    async def remove_response(self, resp):
        """ Move a response to the history directory. """
        history = self.port/"history"
        while True:
            history_name = f"{time.time():.2f}-{resp.name}"
            try:
                # we could do this as async IO, seems unnecessary
                resp.rename(history/history_name)
                break
            except FileExistsError:
                pass

    async def make_request(self, config=None):
        """ Make a complete request and wait for the response. """
        # FIXME this is not functional as is
        req = await self.prepare_request(config)
        # client would put request content
        await self.send_request(req)
        resp, status = await self.wait_for_response(req)
        if status == "error":
            await self.response_error(resp)
        # client would get response content
        await self.remove_response(resp)   # TODO we probably don't want to remove it here
        return resp, status

# Note: Although some methods do not make any async calls,
# we made them all async for consistency and future-proofing.
