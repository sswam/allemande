from datetime import datetime
import re

from settings import PATH_HOME, PATH_ROOMS


def usage_log(user: str|None, ts: datetime, duration: float, service: str, model: str, agent: str, room: str, input_count: int, output_count: int, cost: float, error: str) -> None:
    """ Log usage """
    month = ts.strftime("%Y-%m")
    if user in [None, "system"]:
        log_file = PATH_HOME/f"usage_unknown.{month}.log"
    else:
        user = re.sub(r"=.*", "", user)
        log_file = PATH_ROOMS/user/f"usage.{month}.log"
    duration_str = f"{duration:.6f}".rstrip('0').rstrip('.')
    cost_str = f"{cost:.8f}".rstrip('0').rstrip('.')
    error = re.sub(r"[\t\n]", "  ", error)
    with open(log_file, "a") as f:
        f.write(f"{ts}\t{duration_str}\t{service}\t{model}\t{agent}\t{room}\t{input_count}\t{output_count}\t{cost_str}\t{error}\n")
