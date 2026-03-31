from dataclasses import dataclass
import argparse
from typing import Any, DefaultDict

import ally_agents
import ally_room

@dataclass
class Skip:
    skip: int = 0
    autopoke: int = 0

@dataclass
class Context:
    agents: ally_agents.Agents
    file: str
    args: argparse.Namespace
    history: list[str]
    history_start: int
    mission: list[str]
    summary: list[str]
    config: dict[str, Any]
    responsible_human: str|None
    poke: bool
    skip: Skip|None
    room: ally_room.Room
    local_visual_dir: str|None
