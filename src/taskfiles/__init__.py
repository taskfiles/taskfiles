import ast
import importlib
import logging
import os
import pkgutil
import sys
from types import ModuleType
from typing import Dict, Iterator

from invoke.collection import Collection, Task
from path import Path

try:
    TASKS_KEEP_MODULE_NAME_PREFIX = ast.literal_eval(
        os.environ.get("TASKS_KEEP_MODULE_NAME_PREFIX", "False")
    )
except Exception as error:
    logging.error(f"Reading env var TASKS_KEEP_MODULE_NAME_PREFIX: {error}")
    TASKS_KEEP_MODULE_NAME_PREFIX = False

try:
    TASKS_LOAD_PLUGINS = bool(ast.literal_eval(os.getenv("TASKS_LOAD_PLUGINS", "True")))
except Exception as error:
    logging.error(f"Reading env var TASKS_LOAD_PLUGINS: {error}")
    TASKS_LOAD_PLUGINS = False


try:
    TASKS_PLUGIN_DIRS_ = os.getenv("TASKS_PLUGIN_DIRS", "")
    if isinstance(TASKS_PLUGIN_DIRS_, str):
        TASKS_PLUGIN_DIRS = TASKS_PLUGIN_DIRS_.split(":")
except Exception:
    TASKS_PLUGIN_DIRS = []


def import_submodules(package_name) -> Dict[str, ModuleType]:
    """
    Import all submodules of a module, recursively

    :param package_name: Package name
    :type package_name: str
    :rtype: dict[types.ModuleType]
    """
    package = sys.modules[package_name]
    result = {}
    for _loader, name, _is_pkg in pkgutil.walk_packages(package.__path__):
        try:
            result[name] = importlib.import_module(package_name + "." + name)
        except (ImportError, SyntaxError) as error:
            logging.error(f"Error loading {name}: {error}")

    return result


def iter_tasks_module(
    module: ModuleType,
) -> Iterator[Task]:
    """
    Returns True if any successful additions happened
    """
    for _, maybe_task in module.__dict__.items():
        if not isinstance(maybe_task, Task):
            continue
        yield maybe_task


def get_root_ns(split=TASKS_KEEP_MODULE_NAME_PREFIX, cwd=None) -> Collection:
    """
    Loads built-in tasks, then loads local_tasks.py and finally loads plugins
    if enabled.
    """
    # Built-in
    all_submodules = import_submodules("taskfiles")

    valid_submodules = {
        name: value for name, value in all_submodules.items() if not name.startswith("_")
    }
    ns = Collection()
    for name, submodule in valid_submodules.items():
        logging.debug(f"Loading built-in module {name}")
        if split:
            ns.add_collection(Collection.from_module(submodule))
        else:
            for task in iter_tasks_module(submodule):
                ns.add_task(task)
    # Local tasks
    cwd = cwd or os.getcwd()
    local_tasks_repr = Path(cwd) / "local_tasks.py"
    try:
        import local_tasks
    except ImportError:
        logging.debug(f"{local_tasks_repr} not found in {os.getcwd()}")
    except Exception as error:
        logging.error(f"Error importing {local_tasks_repr}: {error}")
    else:
        for task in iter_tasks_module(local_tasks):
            ns.add_task(task)

    # Load plugins
    if "__file__" in globals():
        # Not binary discovery
        topdir = Path(__file__).parent
        _plugins = topdir / "_plugins"

    else:
        logging.warning("Don't know how to load local plugins in this modality")
    return ns