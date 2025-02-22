#!/usr/bin/env python3-allemande

"""
Switch between PulseAudio outputs.
"""

import os
import json
from pathlib import Path
import pulsectl  # type: ignore
import shutil
import sh

from ally import main, logs  # type: ignore

__version__ = "0.1.3"

logger = logs.get_logger()


def get_state_file() -> Path:
    """Get the path to the state file."""
    return Path.home() / ".local" / "state" / "pulse_audio_toggle.json"


def load_state() -> int:
    """Load the previous sink number from state file."""
    state_file = get_state_file()
    try:
        return json.loads(state_file.read_text())["prev_sink"]
    except (json.JSONDecodeError, FileNotFoundError, PermissionError, KeyError):
        logger.warning("Invalid state file, using default")
        return 0


def save_state(prev_sink: int) -> None:
    """Save the previous sink number to state file."""
    state_file = get_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps({"prev_sink": prev_sink}))


def get_sink_info(pulse: pulsectl.Pulse, index: int) -> str:
    """Get formatted sink info string."""
    for sink in pulse.sink_list():
        if sink.index == index:
            return f"{index}\t{sink.description}"
    return ""


def list_sinks(pulse: pulsectl.Pulse, curr_sink: int) -> None:
    """List all available sinks."""
    for sink in pulse.sink_list():
        prefix = "*" if sink.index == curr_sink else " "
        print(f"{prefix} {sink.index}\t{sink.description}")


def get_current_sink(pulse: pulsectl.Pulse) -> int:
    """Get the current sink index."""
    curr_sink_name = pulse.server_info().default_sink_name
    for sink in pulse.sink_list():
        if sink.name == curr_sink_name:
            return sink.index
    raise RuntimeError("Could not find current sink")


def show_sink_info(pulse: pulsectl.Pulse, sink_set: int) -> None:
    """Show sink info for the given sink index."""
    info = get_sink_info(pulse, sink_set)
    print(info)
    _index, description = info.split("\t", 1)
    if os.environ.get("DISPLAY") and shutil.which("notify-send"):
        sh.notify_send("audio output device", description, t=1000)

def pulse_audio_toggle(sink_set: int | None = None, list_: bool = False, info: bool = False) -> None:
    """Switch between PulseAudio outputs."""
    with pulsectl.Pulse("pulse_audio_toggle") as pulse:
        curr_sink = get_current_sink(pulse)

        if info:
            print(get_sink_info(pulse, curr_sink))
            return

        if list_:
            list_sinks(pulse, curr_sink)
            return

        prev_sink = load_state()

        if sink_set is not None:
            if sink_set == curr_sink:
                logger.info("Already using sink: %d", sink_set)  # Fixed f-string logging
                return

            # Find sink object by index
            target_sink = next((s for s in pulse.sink_list() if s.index == sink_set), None)
            if target_sink is None:
                raise ValueError(f"Invalid sink number: {sink_set}")

            prev_sink = curr_sink
            pulse.sink_default_set(target_sink.name)  # Use sink name instead of index
            save_state(prev_sink)
            show_sink_info(pulse, sink_set)
            return

        if prev_sink == curr_sink:
            logger.info("Already using sink: %d", curr_sink)  # Fixed f-string logging
            return

        # Find sink object by index
        target_sink = next((s for s in pulse.sink_list() if s.index == prev_sink), None)
        if target_sink is not None:
            pulse.sink_default_set(target_sink.name)  # Use sink name instead of index
            save_state(curr_sink)
            show_sink_info(pulse, prev_sink)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("sink_set", nargs="?", type=int, help="output number to switch to")
    arg("-l", "--list", action="store_true", dest="list_", help="list available outputs")
    arg("-i", "--info", action="store_true", help="show current output")


if __name__ == "__main__":
    main.go(pulse_audio_toggle, setup_args)
