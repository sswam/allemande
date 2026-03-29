#!/usr/bin/env python3
"""
Read TSV usage log from stdin and print a cost report.
"""

import os
import sys
import argparse
from collections import defaultdict
from pathlib import Path
from datetime import datetime


def format_cost(cost: float) -> str:
    """Format cost to 6 d.p., stripping trailing zeros and decimal point."""
    return f"{cost:.6f}".rstrip("0").rstrip(".")


def main() -> None:
    parser = argparse.ArgumentParser(description="Usage cost report from TSV stdin")
    parser.add_argument("date0", nargs="?", help="Start date yyyy-mm-dd (inclusive)")
    parser.add_argument("date1", nargs="?", help="End date yyyy-mm-dd (exclusive)")
    parser.add_argument("-a", "--agent", help="Filter by agent (case-insensitive)")
    parser.add_argument("-m", "--model", help="Filter by model (case-insensitive)")
    parser.add_argument("-s", "--service", help="Filter by service (case-insensitive)")
    parser.add_argument("-u", "--user", help="Read from current usage file for user")
    args = parser.parse_args()

    date0 = args.date0
    date1 = args.date1
    agent_filter = args.agent.lower() if args.agent else None
    model_filter = args.model.lower() if args.model else None
    service_filter = args.service.lower() if args.service else None

    total_cost = 0.0
    agents: dict = defaultdict(lambda: {"name": "", "cost": 0.0, "models": set()})

    if args.user:
        now = datetime.now()
        month = now.strftime("%Y-%m")
        file = Path(os.environ["ALLEMANDE_ROOMS"])/args.user/f"usage.{month}.log"
        inp = open(file)
    else:
        inp = sys.stdin

    for line in inp:
        fields = line.rstrip("\n").split("\t")
        if len(fields) < 9:
            continue

        timestamp, _duration, service, model, agent, _room, _in, _out, cost_str = fields[:9]

        if date0 and timestamp[:10] < date0:
            continue
        if date1 and timestamp[:10] >= date1:
            continue
        if agent_filter and agent.lower() != agent_filter:
            continue
        if model_filter and model.lower() != model_filter:
            continue
        if service_filter and service.lower() != service_filter:
            continue

        try:
            cost = float(cost_str)
        except ValueError:
            continue

        total_cost += cost
        key = agent.lower()
        if not agents[key]["name"]:
            agents[key]["name"] = agent
        agents[key]["cost"] += cost
        agents[key]["models"].add(model)

    print(format_cost(total_cost))
    for _key, data in sorted(agents.items(), key=lambda x: x[1]["cost"], reverse=True):
        models_str = ", ".join(sorted(data["models"]))
        print(f"{data['name']}\t{format_cost(data['cost'])}\t{models_str}")


if __name__ == "__main__":
    main()
