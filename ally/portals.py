""" Allemande portals library. """

import os
import time
from pathlib import Path
import logging
import asyncio

import yaml
from watchfiles import awatch, Change

__version__ = "0.1.1"

logger = logging.getLogger(__name__)


def get_default_portal_name(service):
    """ Get the default portal for a server. """
    user_id = os.environ["USER"]
    hostname = os.environ["HOSTNAME"]
    default_portals_dir = Path(os.environ["ALLEMANDE_PORTALS"])/service
    #default_portal_id = f'{user_id}-{os.getpid()}'   # TODO?
    default_portal_id = f'{hostname}_{user_id}'
    default_portal = str(default_portals_dir/default_portal_id)
    return default_portal


# def portal_setup(portal):
# 	""" Set up a portal """
# 	for box in ("prep", "todo", "doing", "done", "error", "history"):
# 		(portal/box).mkdir(exist_ok=True)


class PortalClient:
    """ Client for making requests to the core server. """
    def __init__(self, portal):
        self.portal = Path(portal)
        self.req_id = 0

    async def prepare_request(self, config=None):
        """ Make a request to the core server. """
        prep = self.portal/"prep"
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
        todo = self.portal/"todo"
        # we could do this as async IO, seems unnecessary
        req.rename(todo/req.name)

    async def wait_for_response(self, req, timeout=None):
        """ Wait for a response from the core server with timeout. """
        done = self.portal/"done"
        error = self.portal/"error"

        if timeout is not None:
            timeout = timeout * 1000

        async for changes in awatch(done, error, recursive=False, rust_timeout=timeout, yield_on_timeout=True):
            if not changes:
                raise TimeoutError("Timed out waiting for response")
            for change_type, path in changes:
                if change_type == Change.added:
                    resp = Path(path)
                    if resp.is_dir() and resp.name == req.name:
                        status = resp.parent.name
                        return resp, status

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
        history = self.portal/"history"
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
