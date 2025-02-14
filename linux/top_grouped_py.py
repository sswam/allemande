#!/usr/bin/env python3

"""
Display top processes grouped by executable name, sorted by memory or CPU usage.
"""

import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


@dataclass
class Process:
    """Represents a process with its resource usage information."""

    pid: int
    ppid: int
    cmdline: str
    cmd_name: str
    rss: int
    vsz: int
    pcpu: float
    pmem: float


def get_system_ram() -> int:
    """Get total system RAM in bytes."""
    meminfo = Path("/proc/meminfo").read_text(encoding='utf-8')
    for line in meminfo.splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1])  # in KB


def read_proc_entry(pid: int, total_ram: int) -> Process | None:
    """Read process information from /proc/[pid]."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding='utf-8').split()
        status = Path(f"/proc/{pid}/status").read_text(encoding='utf-8')
        cmdline = Path(f"/proc/{pid}/cmdline").read_text(encoding='utf-8').split('\0')[0]

        # Extract memory info from status
        rss = 0
        vsz = 0
        for line in status.splitlines():
            if line.startswith("VmRSS:"):
                rss = int(line.split()[1])
            elif line.startswith("VmSize:"):
                vsz = int(line.split()[1])

        # Get first word of command line for grouping
        cmd_name = cmdline.split()[0] if cmdline else stat[1].strip('()')

        return Process(
            pid=pid,
            ppid=int(stat[3]),
            cmdline=cmdline or stat[1].strip('()'),
            cmd_name=cmd_name,
            rss=rss,
            vsz=vsz,
            pcpu=float(stat[13]) / 100.0,
            pmem=(float(rss) / total_ram) * 100.0
        )
    except (FileNotFoundError, PermissionError):
        return None


def get_processes(total_ram: int) -> list[Process]:
    """Get list of all running processes."""
    processes = []
    proc = Path("/proc")

    for entry in proc.iterdir():
        if not entry.is_dir() or not entry.name.isdigit():
            continue

        proc_info = read_proc_entry(int(entry.name), total_ram)
        if proc_info:
            processes.append(proc_info)

    return processes


def group_processes(processes: list[Process]) -> dict[str, list[Process]]:
    """Group processes by command name, accumulating values."""
    grouped = defaultdict(list)
    for proc in processes:
        grouped[proc.cmd_name].append(proc)
    groups = []
    for procs in grouped.values():
        group = Process(
            pid=procs[0].pid,
            ppid=procs[0].ppid,
            cmdline=procs[0].cmdline,
            cmd_name=procs[0].cmd_name,
            rss=sum(p.rss for p in procs),
            vsz=sum(p.vsz for p in procs),
            pcpu=sum(p.pcpu for p in procs),
            pmem=sum(p.pmem for p in procs)
        )
        groups.append(group)
    return groups


def output_groups(groups: dict[str, list[Process]], sort_by: str = "rss", limit: int = 20, out: TextIO = sys.stdout) -> None:
    """Output grouped processes sorted by specified metric."""
    # Calculate group totals and sort
    groups.sort(key=lambda x: getattr(x, sort_by), reverse=True)

    # Output header
    print("VSZ(MB)\tRSS(MB)\t%CPU\t%MEM\tCOMMAND", file=out)

    # Output top N groups
    for group in groups[:limit]:
        print(f"{group.vsz / 1024:.0f}\t{group.rss / 1024:.0f}\t{group.pcpu:.1f}\t{group.pmem:.1f}\t{group.cmdline}", file=out)


def top_grouped(sort_by: str = "rss", limit: int = 20, out: TextIO = sys.stdout) -> None:
    """Show top processes grouped by executable name."""
    total_ram = get_system_ram()
    processes = get_processes(total_ram)
    groups = group_processes(processes)
    output_groups(groups, sort_by, limit, out)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-s", "--sort-by", default="rss", choices=["rss", "vsz", "pcpu", "pmem"], help="sort by: rss, vsz, pcpu, or pmem")
    arg("-n", "--limit", type=int, default=20, help="number of processes to show")


if __name__ == "__main__":
    main.go(top_grouped, setup_args)
