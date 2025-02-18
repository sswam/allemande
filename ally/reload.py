import sys
import os
import importlib
import logging


logger = logging.getLogger(__name__)


# The last modification time of reloadable modules
_last_modified: dict[str, float] = {}


def reload_module_if_modified(module_name):
    """
    Checks if the specified module's source file has been modified,
    and reloads it if it has changed.

    Args:
        module_name (str): Name of the module to check and potentially reload

    Returns:
        bool: True if module was reloaded, False otherwise
    """
    try:
        # Get the module object
        module = sys.modules[module_name]

        # Get the path to the module's source file
        module_file = module.__file__

        # Get the current modification time
        current_mtime = os.path.getmtime(module_file)

        # Get the last recorded modification time, if any
        last_mtime = _last_modified.get(module_name, 0)

        # If the file has been modified since last check
        if current_mtime > last_mtime:
            # Reload the module
            importlib.reload(module)

            # Update the last modification time
            _last_modified[module_name] = current_mtime

            logger.info("Reloaded module %s", module_name)
            return True

        return False

    except Exception:  # pylint: disable=broad-except
        logger.exception("Error reloading module %s", module_name)
        return False
