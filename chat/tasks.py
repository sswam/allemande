import asyncio
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


active_tasks: dict[asyncio.Task, str] = {}


def add_task(task: asyncio.Task, description: str):
    """Add a task to the active tasks."""
    active_tasks[task] = description
    task.add_done_callback(task_done_callback)


def task_done_callback(task):
    """Callback for when a task is done."""
    logger.debug("Task done: %r", active_tasks[task])
    del active_tasks[task]
    try:
        task.result()
    except Exception:  # pylint: disable=broad-except
        logger.exception("Task failed", exc_info=True)


async def wait_for_tasks():
    """Wait for all active tasks to complete."""
    logger.info("Waiting for %d active tasks", len(active_tasks))
    while active_tasks:
        await asyncio.gather(*active_tasks.keys())


def list_active_tasks():
    """List the active tasks."""
    logger.info("Active tasks: %d", len(active_tasks))
    for description in active_tasks.values():
        logger.info("  - %s", description)
