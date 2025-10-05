#!/usr/bin/env python3-allemande

from settings import *
from ally_agents import Agents, Agent

def local_agent():
    return

def remote_agent():
    return

def run_safe_shell():
    return

def run_tool():
    return

def run_search():
    return

def run_python():
    return

services = {
    "llm_llama":    {"link": "portal", "fn": local_agent},
    "image_a1111":  {"link": "portal", "fn": local_agent, "dumb": True},
    "image_openai": {"link": "remote", "fn": remote_agent, "dumb": True},  # TODO
    "openai":       {"link": "remote", "fn": remote_agent},
    "anthropic":    {"link": "remote", "fn": remote_agent},
    "google":       {"link": "remote", "fn": remote_agent},
    "perplexity":   {"link": "remote", "fn": remote_agent},
    "xai":          {"link": "remote", "fn": remote_agent},
    "deepseek":     {"link": "remote", "fn": remote_agent},
    "openrouter":   {"link": "remote", "fn": remote_agent},
    "venice":       {"link": "remote", "fn": remote_agent},
    "safe_shell":   {"link": "tool", "fn": run_safe_shell, "safe": False, "dumb": True},  # ironically
    "tool":         {"link": "tool", "fn": run_tool, "dumb": True},
    "search":       {"link": "tool", "fn": run_search, "dumb": True},
    "python":       {"link": "tool", "fn": run_python, "dumb": True},
}

if __name__ == "__main__":
    agents = Agents(services)
    agents.load(PATH_AGENTS/"over")
    agents.load(PATH_AGENTS/"base")
    agents.load(PATH_AGENTS/"character")
    # rooms_public_agents = PATH_ROOMS/"agents"
    # agents.load(rooms_public_agents)
