"""This module contains the classes for the agents in the Allemande system"""

import os
import logging
from pathlib import Path
import yaml
from watchfiles import Change
import re
from copy import deepcopy
from typing import Any

from deepmerge import always_merger, Merger, STRATEGY_END

from ally.cache import cache  # type: ignore
from safety import safety  # type: ignore
import chat


logger = logging.getLogger(__name__)

# Constants, TODO shared
PATH_VISUAL = Path(os.environ["ALLEMANDE_VISUAL"])

ADULT = os.environ.get("ALLYCHAT_ADULT", "0") == "1"
SAFE = os.environ.get("ALLYCHAT_SAFE", "1") == "1"


# - TODO:
#   - if first element of list is "+" we extend, else overwrite.
#   - if first element is "U" we add and deduplicate, like set union.
#   - s/foo/bar
#   - =foo to pass foo through literally as a string without changes
#   - ["=", ...] means pass the rest of the list through without changes

def merge_string_strategy(config, path, base, nxt):
    """A strategy to merge strings with support for '+' prefix"""
    if isinstance(base, str) and isinstance(nxt, str):
        if nxt.startswith("+"):
            # check followed by whitespace or end of string
            if len(nxt) == 1 or nxt[1].isspace():
                return base + nxt[1:]
            return base + " " + nxt[1:]
        return nxt
    return STRATEGY_END

# Create a custom merger with specific strategies for different types
agent_merger = Merger(
    # Type-specific strategies
    [
        (dict, ["merge"]),  # Merge dictionaries
        (list, ["append"]), # Append lists
        (str, merge_string_strategy), # Custom string merging
    ],
    # Fallback strategy for other types
    ["override"],
    # Strategy for type conflicts
    ["override"]
)


class Agents:
    pass


class Agent:
    """An Allemande Agent"""
    def __init__(self, data: dict = None, agents: Agents = None, file: Path = None):
        self.agents = agents
        if file and data:
            raise ValueError("Cannot specify both file and data")
        if data:
            self.data = data
        else:
            self.load_agent(file)
        self.name = self.data["name"]

    def load_agent(self, file: Path) -> None:
        """Load the agent data from a file."""
        name = file.stem
        with open(file, encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

        if "name" not in self.data:
            self.data["name"] = name
        elif self.data["name"].lower() != name.lower():
            raise ValueError(f'Agent name mismatch: {name} vs {self.data["name"]}')

    def copy(self):
        """Return a copy of the agent"""
        return Agent(data=deepcopy(self.data), agents=self.agents)

    def get(self, key: str, default=None, raise_error=False):
        """Get a value from the agent's data"""
        base = self.base()
        if key not in self.data and base:
            value = base.get(key, default, raise_error)
        elif key not in self.data and raise_error:
            raise KeyError(key)
        else:
            value = self.data.get(key, default)

            # if dict or list, deep merge with base agent's value
            # This will extend lists and merge dictionaries
            # Extending lists might not always be the desired behavior, we'll see
            # TODO reduce indent here
            if base:
                base_value = deepcopy(base.get(key))
                value = agent_merger.merge(base_value, value)

#             if base and isinstance(value, (dict, list)):
#                 base_value = base.get(key)
#                 if isinstance(base_value, type(value)):
#                     value = agent_merger.merge(deepcopy(base_value), value)

        # replace $NAME, $FULLNAME and $ALIAS in the agent's prompts
        # We do this on get, rather than initially, because we can define
        # a derived agent with different names.
        # TODO do this more generally for other variables?
        if value and key in ["system_top", "system_bottom"]:
            name = self.get("name")
            fullname = self.get("fullname", name)
            aliases = self.get("aliases") or [name]
            aliases_or = ", ".join(aliases[:-1]) + " or " + aliases[-1] if len(aliases) > 1 else aliases[0]
            value = re.sub(r"\$NAME\b", name, value)
            value = re.sub(r"\$FULLNAME\b", fullname, value)
            value = re.sub(r"\$ALIAS\b", aliases_or, value)

        # TODO remove null values? i.e. enable to remove an attribute from base

        return value

    def base(self):
        """Get the base agent"""
        base_name = self.data.get("base")
        if base_name == "super" and self.agents.parent:
            return self.agents.parent.get(self.name)
        if base_name:
            return self.agents.get(base_name)
        return None

    def set(self, key: str, value):
        """Set a value in the agent's data"""
        self.data[key] = value

    def __getitem__(self, key: str):
        """Enable dictionary-style access using square brackets"""
        return self.get(key, raise_error=True)

    def __setitem__(self, key: str, value):
        """Enable dictionary-style value setting using square brackets"""
        self.data[key] = value

    def __contains__(self, key: str):
        """Check if the agent's data contains a key"""
        try:
            return self[key]
        except KeyError:
            return False

    def update(self, data: dict):
        """Update the agent's data"""
        self.data.update(data)

    def get_all_names(self) -> list[str]:
        """Get all the names for this agent."""
        agent_names = [self.name]
        fullname = self.get("fullname")
        if fullname:
            agent_names.append(fullname)
            if " " in fullname:
                agent_names.append(fullname.split(" ")[0])
        agent_names.extend(self.get("aliases", []))
        return agent_names

    def set_up(self, services: dict[str, Any]) -> bool:
        """Set up an agent"""

        agent_type = self.get("type")
        if agent_type in ["human", "visual"]:
            return False

        service = services.get(agent_type)

        if service is None:
            raise ValueError(f'Unknown service for agent: {self["name"]}, {agent_type}')

        self.update(service)

        if SAFE and not self.get("safe", True):
            return False

        if not ADULT and self.get("adult"):
            return False

        self.data = safety.apply_or_remove_adult_options(self.data, ADULT)

        self.setup_maps()

        return True

    def update_visual(self):
        """Update the visual prompts for an agent."""
        visual = self.get("visual")
        logger.debug("update_visual: %r %r", self.name, visual)
        if not visual:
            return

        name_lc = self.name.lower()
        all_names = self.get_all_names()

        # TODO reduce indent here

        # supporting arbitrary keys might be a security risk
        for key in "person", "clothes", "age", "emo":
            if key not in visual:
                cache.remove(str(PATH_VISUAL / key / name_lc) + ".txt")
                for name in all_names:
                    for dest in name, name.lower():
                        cache.remove(str(PATH_VISUAL / key / dest) + ".txt")
                continue

            prompt = visual.get(key)
            if prompt:
                path = key if key == "person" else "person/" + key
                prompt = str(prompt).strip() + "\n"
                (PATH_VISUAL / path).mkdir(parents=True, exist_ok=True)
                cache.save(str(PATH_VISUAL / path / name_lc) + ".txt",
                        prompt, noclobber=False)
                cache.chmod(str(PATH_VISUAL / path / name_lc) + ".txt", 0o664)

                # symlink main file to agent's other names
                for name in all_names:
                    for dest in name, name.lower():
                        if dest == name_lc:
                            continue
                        cache.symlink(name_lc + ".txt",
                                str(PATH_VISUAL / path / dest) + ".txt")

    def remove_visual(self):
        """Remove the visual prompts for an agent."""
        all_names = self.get_all_names()

        for key in "person", "person/clothes":
            for name in all_names:
                for dest in name, name.lower():
                    try:
                        cache.remove(str(PATH_VISUAL / key / dest) + ".txt")
                    except FileNotFoundError:
                        pass

    def setup_maps(self):
        """Setup maps for an agent"""
        data = self.data
        for k in "input_map", "output_map", "map", "map_cs", "input_map_cs", "output_map_cs":
            if k not in data:
                data[k] = {}
        for k, v in data["input_map"].items():
            k_lc = k.lower()
            if k == k_lc:
                continue
            del data["input_map"][k]
            data["input_map"][k_lc] = v
        for k, v in data["output_map"].items():
            k_lc = k.lower()
            if k == k_lc:
                continue
            del data["output_map"][k]
            data["output_map"][k_lc] = v
        for k, v in data["map"].items():
            k_lc = k.lower()
            v_lc = v.lower()
            if k_lc not in data["input_map"]:
                data["input_map"][k_lc] = v
            if v_lc not in data["output_map"]:
                data["output_map"][v_lc] = k
        for k, v in data["map_cs"].items():
            if k not in data["input_map_cs"]:
                data["input_map_cs"][k] = v
            if v not in data["output_map_cs"]:
                data["output_map_cs"][v] = k


class Agents:
    """A collection of agents"""

    def __init__(self, services: dict[str, Any], parent: Agents|None=None):
        self.agents: dict[str, Agent] = {}
        self.services: dict[str, Any] = services
        self.parent: Agents = parent

    def write_agents_list(self, path: str):
        """Write the list of agents to a file."""
        agent_names = sorted(set(agent.name for agent in self.agents.values()))
        cache.save(path, agent_names, noclobber=False)

    def load_agent_without_setup(self, agent_file: Path) -> Agent | None:
        """Load an agent from a file."""
        name = agent_file.stem
        self.remove_agent(name)

        agent = Agent(file=agent_file, agents=self)

        # Add agent under all its names
        all_names = agent.get_all_names()
        for name_lc in map(str.lower, all_names):
            if name_lc in self.agents:
                if self.agents[name_lc] != agent:
                    old_main_name = self.agents[name_lc].name
                    logger.warning("Agent name conflict: %r vs %r for %r",
                                old_main_name, agent.name, name_lc)
                continue
            self.agents[name_lc] = agent

        return agent

    def remove_agent(self, name: str):
        """Remove an agent."""
        agent = self.agents.get(name.lower())
        if not agent:
            return
        agent_names = agent.get_all_names()
        for name_lc in map(str.lower, agent_names):
            self.agents.pop(name_lc, None)

        agent.remove_visual()

    def load(self, path: Path):
        """Load all agents or one agent from a path."""
        if path.is_dir():
            agent_files = path.glob("*.yml")
        else:
            agent_files = [path]

        new_agents = []

        # load all agents first
        for agent_file in agent_files:
            try:
                agent = self.load_agent_without_setup(agent_file)
                new_agents.append(agent)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Error loading agent", exc_info=True)

        # then set up and update visuals
        for agent in new_agents:
            agent_type = agent.get("type")
            if not agent.set_up(self.services):
                self.remove_agent(agent.name)
                continue
            agent.update_visual()

    def handle_file_change(self, file_path: str, change_type: Change):
        """Process an agent file change."""
        if change_type == Change.deleted:
            name = Path(file_path).stem
            logger.info("Removing agent: %r", name)
            self.remove_agent(name)
        else:
            logger.info("Loading agent: %r", file_path)
            self.load(Path(file_path))

    def items(self):
        """Get the agents as a list of tuples."""
        pairs = list(self.agents.items())
        if self.parent:
            for name, agent in self.parent.items():
                if name not in self.agents:
                    pairs.append((name, agent))
        return pairs

    def names(self) -> list[str]:
        """Get the names of the agents."""
        keys = set(self.agents.keys())
        if self.parent:
            keys.update(self.parent.names())
        return list(keys)

    def get(self, name: str) -> Agent | None:
        """Get an agent by name."""
        name_lc = name.lower()
        if name_lc in self.agents:
            return self.agents[name_lc]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name: str, agent: Agent):
        """Set an agent."""
        self.agents[name.lower()] = agent

    def __contains__(self, name: str):
        """Check if an agent is in the collection."""
        return self.get(name) is not None
