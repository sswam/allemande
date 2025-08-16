"""This module contains the classes for the agents in the Allemande system"""

import os
import logging
from pathlib import Path
from copy import deepcopy
from typing import Any
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import yaml
from watchfiles import Change
from deepmerge import Merger, STRATEGY_END

from ally.cache import cache  # type: ignore
from ally.util import replace_variables  # type: ignore
from safety import safety  # type: ignore
from util import uniqo


logger = logging.getLogger(__name__)

# Constants, TODO shared
VISUAL_KEYS = ["person", "clothes", "clothes_upper", "clothes_lower", "age", "emo", "furry", "pony"]
PATH_VISUAL = Path(os.environ["ALLEMANDE_VISUAL"])

ADULT = os.environ.get("ALLYCHAT_ADULT", "0") == "1"
SAFE = os.environ.get("ALLYCHAT_SAFE", "1") == "1"


# - TODO:
#   - if first element of list is "+" we extend, else overwrite.
#   - if first element is "U" we add and deduplicate, like set union.
#   - s/foo/bar
#   - =foo to pass foo through literally as a string without changes
#   - ["=", ...] means pass the rest of the list through without changes

def merge_string_strategy(_config, _path, base, nxt):
    """A strategy to merge strings with support for '+' prefix and suffix."""
    if not (isinstance(base, str) and isinstance(nxt, str)):
        return STRATEGY_END
    if nxt.startswith("+"):
        # check followed by whitespace or end of string
        if len(nxt) == 1 or nxt[1].isspace():
            return base + nxt[1:]
        return base + " " + nxt[1:]
    if nxt.endswith("+") or nxt.endswith("+\n"):
        # check preceded by whitespace
        nxt = nxt[:nxt.rfind("+")]
        if not nxt or nxt[-1].isspace():
            return nxt + base
        return nxt + " " + base
    return nxt

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
    pass


class NotEnabledError(Exception):
    pass


class Agent:
    """An Allemande Agent"""
    def __init__(self, data: dict|None = None, agents: Agents|None = None, file: Path|None = None, private: bool=False):
        self.agents = agents
        if file and data:
            raise ValueError("Cannot specify both file and data")
        if not file and not data:
            raise ValueError("Must specify either file or data")
        if data:
            self.data = data
        if file:
            self.load_agent(file)
        self.name = self.data["name"]
        self.private = private
        if private:
            self.data = {k: self.data[k] for k in ("visual", "name", "fullname", "aliases") if k in self.data}
            self.data["type"] = "visual"
        self.nsfw = False
        if file and file.parent.name == "nsfw":
            self.data["adult"] = True

    def load_agent(self, file: Path) -> None:
        """Load the agent data from a file."""
        name = file.stem
        with open(file, encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

        if self.data is None:
            raise ValueError(f"Agent file {file} is empty or invalid")

        if self.data.get("enabled", True) is False:
            raise NotEnabledError(f"Agent is not enabled: {file}")

        if "name" not in self.data:
            self.data["name"] = name
        elif self.data["name"] != name:
            raise ValueError(f'Agent name mismatch: {name} vs {self.data["name"]}')

    def copy(self) -> Agent:
        """Return a copy of the agent"""
        return Agent(data=deepcopy(self.data), agents=self.agents)

    def apply_identity(self, reference: Agent) -> Agent:
        """Create a new agent based on self with name and other attributes from reference."""
        data = {
            "base": [self.name],
        }
        for key in ["name", "fullname", "aliases", "age", "visual"]:
            if key in reference.data:
                data[key] = deepcopy(reference.data[key])
        agent = Agent(data=data, agents=self.agents)
        return agent

    def get(self, key: str, default=None, raise_error=False, raw=False, room: str|None = None, with_over: bool=True):
        """Get a value from the agent's data"""
        base = self.base()
        over = self.over() if with_over else []

        value = None

        objects = base + [self]
        if key not in ["name", "fullname"]:
            objects += over

        for obj in objects:
            if obj == self:
                value2 = self.data.get(key)
            else:
                use_over = with_over and obj not in base
                value2 = obj.get(key, raw=True, with_over=use_over)
            if value is not None and value2 is not None:
                value2 = agent_merger.merge(deepcopy(value), value2)
            if value2 is not None:
                value = value2

        if value is None and raise_error:
            raise KeyError(key)
        if value is None:
            value = default

        if raw:
            return value

        # replace $NAME, $FULLNAME and $ALIAS in the agent's prompts
        # replace $DATE, $TIME, $TZ and $TIMESTAMP with the current time
        # We do this on get, rather than initially, because we can define
        # a derived agent with different names.
        # TODO do this more generally for other variables?
        # replace $ROOM with the room name
        if value and key in ["system_top", "system_bottom"]:
            name = self.get("name")
            fullname = self.get("fullname", name)
            aliases = self.get("aliases") or [name]
            aliases_or = ", ".join(aliases[:-1]) + " or " + aliases[-1] if len(aliases) > 1 else aliases[0]

            tz_name = self.get("timezone", "UTC")
            tz: timezone|ZoneInfo = timezone.utc
            if tz_name != "UTC":
                tz = ZoneInfo(tz_name)

            # tz_offset = timezone(timedelta(hours=11))  # or timezone(timedelta(seconds=11*3600))

            now = datetime.now(tz)
            date = now.strftime("%Y-%m-%d")
            time = now.strftime("%H:%M:%S")
            tz_str = now.strftime("%Z")
            timestamp = f"{date} {time} {tz_str}"
            value = replace_variables(value, {
                "NAME": name,
                "FULLNAME": fullname,
                "ALIAS": aliases_or,
                "DATE": date,
                "TIME": time,
                "TZ": tz_str,
                "TIMESTAMP": timestamp,
                "ROOM": room or '[unknown]',
            })

        # TODO remove null values? i.e. enable to remove an attribute from base

        return value

    def base(self):
        """Get the base agents"""
        base_names = self.data.get("base", [])
        if base_names and isinstance(base_names, str):
            base_names = [base_names]
        base = []
        for name in base_names:
            if name == "super" and self.agents.parent:
                agent = self.agents.parent.get(self.name)
            else:
                agent = self.agents.get(name)
            if agent:
                base.append(agent)
        return base

    def over(self):
        """Get the over agents"""
        over_names = self.get("over", [], with_over=False)
        if over_names and isinstance(over_names, str):
            over_names = [over_names]
        over = []
        for name in over_names:
            agent = self.agents.get(name)
            if agent:
                over.append(agent)
        return over

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
        if key in self.data:
            return True
        base = self.base()
        over = self.over()
        for obj in base + over:
            if key in obj:
                return True
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
                firstname = fullname.split(" ")[0]
                if firstname:
                    agent_names.append(firstname)
        agent_names.extend(self.get("aliases", []))
        return agent_names

    def set_up(self, services: dict[str, Any]) -> bool:
        """Set up an agent"""

        agent_type = self.get("type")
        # if not agent_type or agent_type in ["human", "visual"]:
        #     return False

        if agent_type and agent_type not in ["human", "visual"]:
            service = services.get(agent_type)

            if service is None:
                logger.error("Unknown service for agent: %r, %s", self.name, agent_type)
                return False

            self.update(service)

        if SAFE and not self.get("safe", True):
            return False

        if not ADULT and self.get("adult"):
            return False

        self.data = safety.apply_or_remove_adult_options(self.data, ADULT)

        return True

    def update_visual(self, private: bool=False):
        """Update the visual prompts for an agent."""
        visual = self.get("visual")
        logger.debug("update_visual: %r %r", self.name, visual)
        if not visual:
            return

        all_names = self.get_all_names()

        all_names_with_lc = uniqo(all_names + [name.lower() for name in all_names])

        if private:
            agent1 = self.agents.get(self.name)
            if agent1 and not agent1.private:
                logger.warning("Name conflict between private and public agent: %r", self.name)
                return

        # supporting arbitrary keys might be a security risk
        for key in VISUAL_KEYS:
            prompt = visual.get(key, "")
            path = key if key == "person" else "person/" + key
            prompt = str(prompt).strip() + "\n"
            (PATH_VISUAL / path).mkdir(parents=True, exist_ok=True)
            cache.save(str(PATH_VISUAL / path / self.name) + ".txt",
                    prompt, noclobber=False)
            cache.chmod(str(PATH_VISUAL / path / self.name) + ".txt", 0o664)

            # symlink main file to agent's other names
            for name1 in all_names_with_lc:
                if name1 == self.name:
                    continue
                if private:
                    agent1 = self.agents.get(name1)
                    if agent1 and not agent1.private:
                        logger.warning("Alias conflict for private agent: %r, %r", self.name, name1)
                        continue
                cache.symlink(self.name + ".txt",
                        str(PATH_VISUAL / path / name1) + ".txt")

    def remove_visual(self, private: bool=False):
        """Remove the visual prompts for an agent."""
        all_names = self.get_all_names()
        all_names_with_lc = uniqo(all_names + [name.lower() for name in all_names])

        for key in VISUAL_KEYS:
            path = key if key == "person" else "person/" + key
            for name1 in all_names_with_lc:
                if private:
                    agent1 = self.agents.get(name1)
                    if agent1 and not agent1.private:
                        continue
                try:
                    cache.remove(str(PATH_VISUAL / path / name1) + ".txt")
                except FileNotFoundError:
                    pass


class Agents:
    """A collection of agents"""

    def __init__(self, services: dict[str, Any], parent: Agents|None=None):
        self.agents: dict[str, Agent] = {}
        self.services: dict[str, Any] = services
        self.parent: Agents|None = parent

    def write_agents_list(self, path: str) -> None:
        """Write the list of agents to a file."""
        agent_names = sorted(set(agent.name for agent in self.agents.values()))
        cache.save(path, agent_names, noclobber=False)

    def load_agent_without_setup(self, agent_file: Path, private: bool=False) -> Agent | None:
        """Load an agent from a file."""
        name = agent_file.stem
        self.remove_agent(name, private=private)

        agent = Agent(file=agent_file, agents=self, private=private)

        # Add agent under all its names
        all_names = agent.get_all_names()
        for name1 in all_names:
            if name1 in self.agents:
                if self.agents[name1] != agent:
                    old_main_name = self.agents[name1].name
                    msg_private = " for private agent" if private else ""
                    logger.warning("Agent name conflict%s: %r vs %r for %r",
                            msg_private, old_main_name, agent.name, name1)
                continue
            self.agents[name1] = agent

        return agent

    def remove_agent(self, name: str, keep_visual: bool=False, private: bool=False) -> None:
        """Remove an agent."""
        agent = self.agents.get(name)
        if not agent:
            return

        if not keep_visual:
            agent.remove_visual(private=private)

        agent_names = agent.get_all_names()
        logger.debug("remove_agent: %r", name)
        for name1 in agent_names:
            if private:
                agent1 = self.agents.get(name1)
                if agent1 and not agent1.private:
                    continue
            logger.debug("Removing agent by name: %r", name1)
            self.agents.pop(name1, None)

    def load(self, path: Path, visual: bool=True, private: bool=False) -> None:
        """Load all agents or one agent from a path."""
        if path.is_dir():
            agent_files = list(path.rglob("*.yml"))
        else:
            agent_files = [path]

        new_agents = []

        # load all agents first
        for agent_file in agent_files:
            try:
                agent = self.load_agent_without_setup(agent_file, private=private)
                new_agents.append(agent)
            except NotEnabledError:
                logger.info("Agent not enabled: %s", agent_file)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Error loading agent from %s", agent_file, exc_info=True)

        # then set up and update visuals
        for agent in new_agents:
            if visual:
                agent.update_visual(private=private)
            if not agent.set_up(self.services):
                self.remove_agent(agent.name, keep_visual=True, private=private)
                continue

    def handle_file_change(self, file_path: str, change_type: Change, private: bool=False) -> None:
        """Process an agent file change."""
        if change_type == Change.deleted:
            name = Path(file_path).stem
            logger.info("Removing agent: %r", name)
            self.remove_agent(name, private=private)
        else:
            logger.info("Loading agent: %r", file_path)
            self.load(Path(file_path), private=private)

    def items(self) -> list[tuple[str, Agent]]:
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
        if name in self.agents:
            return self.agents[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name: str, agent: Agent):
        """Set an agent."""
        self.agents[name] = agent

    def __contains__(self, name: str) -> bool:
        """Check if an agent is in the collection."""
        return self.get(name) is not None
