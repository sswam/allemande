#!/usr/bin/env python3-allemande
# pylint: disable=unused-argument

""" Ally Chat test script for debugging agents """

import logging
from pathlib import Path
import re
from typing import Any


import ally_agents
import remote_agents
import local_agents
import settings


logger = logging.getLogger(__name__)


services: dict[str, dict[str, Any]] = {}


def run_safe_shell():
    pass


def run_tool():
    pass


def run_search():
    pass


def run_python():
    pass

def setup_services():
    global services
    services = {
        "llm_llama":    {"link": "portal", "fn": local_agents.local_agent},
        "image_a1111":  {"link": "portal", "fn": local_agents.local_agent, "dumb": True},
        "image_openai": {"link": "remote", "fn": remote_agents.remote_agent, "dumb": True},  # TODO
        "openai":       {"link": "remote", "fn": remote_agents.remote_agent},
        "anthropic":    {"link": "remote", "fn": remote_agents.remote_agent},
        "google":       {"link": "remote", "fn": remote_agents.remote_agent},
        "perplexity":   {"link": "remote", "fn": remote_agents.remote_agent},
        "xai":          {"link": "remote", "fn": remote_agents.remote_agent},
        "deepseek":     {"link": "remote", "fn": remote_agents.remote_agent},
        "openrouter":   {"link": "remote", "fn": remote_agents.remote_agent},
        "venice":       {"link": "remote", "fn": remote_agents.remote_agent},
        "safe_shell":   {"link": "tool", "fn": run_safe_shell, "safe": False, "dumb": True},  # ironically
        "tool":         {"link": "tool", "fn": run_tool, "dumb": True},
        "search":       {"link": "tool", "fn": run_search, "dumb": True},
        "python":       {"link": "tool", "fn": run_python, "dumb": True},
    }


setup_services()


# Load global base agents only
agents = ally_agents.Agents(services)
agents.load(settings.PATH_AGENTS)  # Core agents
